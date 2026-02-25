from collections import defaultdict
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.models import Lead, LeadStatusHistory, PayPeriod, PayrollEntry, PayrollRun, Rep, RepBonusOverride, Status, StatusBonusRule


def run_payroll(db: Session, pay_period_id: int) -> PayrollRun:
    pay_period = db.query(PayPeriod).filter(PayPeriod.id == pay_period_id).first()
    if not pay_period:
        raise ValueError("Pay period not found")
    if pay_period.locked:
        raise ValueError("Pay period is locked")

    start_dt = datetime.combine(pay_period.start_date, time.min)
    end_dt = datetime.combine(pay_period.end_date, time.max)

    status_rows = (
        db.query(LeadStatusHistory, Lead)
        .join(Lead, Lead.id == LeadStatusHistory.lead_id)
        .filter(LeadStatusHistory.changed_at >= start_dt)
        .filter(LeadStatusHistory.changed_at <= end_dt)
        .all()
    )

    reps = {rep.id: rep for rep in db.query(Rep).filter(Rep.is_active.is_(True)).all()}
    bonus_totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))

    for status_event, lead in status_rows:
        rep_id = status_event.changed_by_rep_id or lead.assigned_rep_id
        if not rep_id or rep_id not in reps:
            continue

        override = (
            db.query(RepBonusOverride)
            .filter(RepBonusOverride.rep_id == rep_id, RepBonusOverride.status_id == status_event.status_id)
            .first()
        )
        if override:
            bonus = Decimal(str(override.bonus_amount))
        else:
            rule = (
                db.query(StatusBonusRule)
                .filter(StatusBonusRule.status_id == status_event.status_id, StatusBonusRule.role_type == reps[rep_id].role_type)
                .first()
            )
            bonus = Decimal(str(rule.bonus_amount)) if rule else Decimal("0")

        bonus_totals[rep_id] += bonus

    payroll_run = PayrollRun(pay_period_id=pay_period_id)
    db.add(payroll_run)
    db.flush()

    for rep_id, rep in reps.items():
        base_pay = Decimal(str(rep.base_pay))
        total_bonus = bonus_totals[rep_id]
        total_comp = base_pay + total_bonus
        entry = PayrollEntry(
            payroll_run_id=payroll_run.id,
            rep_id=rep_id,
            base_pay=base_pay,
            total_bonus=total_bonus,
            total_compensation=total_comp,
        )
        db.add(entry)

    db.commit()
    db.refresh(payroll_run)
    return payroll_run


def get_conversion_report(db: Session) -> dict[str, float]:
    total_leads = db.query(Lead).count()
    won_status = db.query(Status).filter(Status.code == "WON").first()
    won_leads = 0
    if won_status:
        won_leads = db.query(LeadStatusHistory.lead_id).filter(LeadStatusHistory.status_id == won_status.id).distinct().count()

    conversion_rate = (won_leads / total_leads * 100) if total_leads else 0.0
    return {"total_leads": total_leads, "won_leads": won_leads, "conversion_rate": round(conversion_rate, 2)}
