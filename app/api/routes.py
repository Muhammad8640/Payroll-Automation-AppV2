import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.models import Lead, LeadStatusHistory, PayPeriod, PayrollEntry, PayrollRun, Rep, RepBonusOverride, Status, StatusBonusRule, User
from app.schemas.schemas import (
    ConversionReport,
    LeadCreate,
    LeadOut,
    LeadStatusHistoryOut,
    LeadStatusUpdate,
    LoginRequest,
    PayPeriodCreate,
    PayPeriodOut,
    PayrollEntryOut,
    RepBonusOverrideCreate,
    RepCreate,
    RepOut,
    StatusBonusRuleCreate,
    StatusCreate,
    StatusOut,
    Token,
    UserCreate,
)
from app.services.payroll import get_conversion_report, run_payroll

router = APIRouter()


@router.post("/auth/register", response_model=dict)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    return {"message": "User created"}


@router.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=create_access_token(user.email))


@router.post("/reps", response_model=RepOut, dependencies=[Depends(require_admin)])
def create_rep(payload: RepCreate, db: Session = Depends(get_db)):
    rep = Rep(**payload.model_dump())
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return rep


@router.get("/reps", response_model=list[RepOut], dependencies=[Depends(require_admin)])
def list_reps(db: Session = Depends(get_db)):
    return db.query(Rep).all()


@router.put("/reps/{rep_id}", response_model=RepOut, dependencies=[Depends(require_admin)])
def update_rep(rep_id: int, payload: RepCreate, db: Session = Depends(get_db)):
    rep = db.query(Rep).filter(Rep.id == rep_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Rep not found")
    for key, value in payload.model_dump().items():
        setattr(rep, key, value)
    db.commit()
    db.refresh(rep)
    return rep


@router.delete("/reps/{rep_id}", dependencies=[Depends(require_admin)])
def delete_rep(rep_id: int, db: Session = Depends(get_db)):
    rep = db.query(Rep).filter(Rep.id == rep_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Rep not found")
    db.delete(rep)
    db.commit()
    return {"message": "Deleted"}


@router.post("/leads", response_model=LeadOut, dependencies=[Depends(require_admin)])
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads", response_model=list[LeadOut], dependencies=[Depends(require_admin)])
def list_leads(db: Session = Depends(get_db)):
    return db.query(Lead).all()


@router.post("/statuses", response_model=StatusOut, dependencies=[Depends(require_admin)])
def create_status(payload: StatusCreate, db: Session = Depends(get_db)):
    status_obj = Status(**payload.model_dump())
    db.add(status_obj)
    db.commit()
    db.refresh(status_obj)
    return status_obj


@router.post("/leads/status", response_model=LeadStatusHistoryOut, dependencies=[Depends(require_admin)])
def add_status_history(payload: LeadStatusUpdate, db: Session = Depends(get_db)):
    history = LeadStatusHistory(**payload.model_dump())
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


@router.post("/bonus-rules", dependencies=[Depends(require_admin)])
def create_bonus_rule(payload: StatusBonusRuleCreate, db: Session = Depends(get_db)):
    rule = StatusBonusRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    return {"message": "Rule created"}


@router.post("/bonus-overrides", dependencies=[Depends(require_admin)])
def create_bonus_override(payload: RepBonusOverrideCreate, db: Session = Depends(get_db)):
    override = RepBonusOverride(**payload.model_dump())
    db.add(override)
    db.commit()
    return {"message": "Override created"}


@router.post("/pay-periods", response_model=PayPeriodOut, dependencies=[Depends(require_admin)])
def create_pay_period(payload: PayPeriodCreate, db: Session = Depends(get_db)):
    pay_period = PayPeriod(**payload.model_dump())
    db.add(pay_period)
    db.commit()
    db.refresh(pay_period)
    return pay_period


@router.post("/payroll/run/{pay_period_id}", dependencies=[Depends(require_admin)])
def payroll_run(pay_period_id: int, db: Session = Depends(get_db)):
    try:
        run = run_payroll(db, pay_period_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"payroll_run_id": run.id, "pay_period_id": run.pay_period_id}


@router.get("/payroll/{pay_period_id}", response_model=list[PayrollEntryOut], dependencies=[Depends(require_admin)])
def payroll_summary(pay_period_id: int, db: Session = Depends(get_db)):
    run = db.query(PayrollRun).filter(PayrollRun.pay_period_id == pay_period_id).order_by(PayrollRun.id.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    rows = (
        db.query(PayrollEntry, Rep)
        .join(Rep, Rep.id == PayrollEntry.rep_id)
        .filter(PayrollEntry.payroll_run_id == run.id)
        .all()
    )
    return [
        PayrollEntryOut(
            rep_id=entry.rep_id,
            rep_name=rep.name,
            base_pay=float(entry.base_pay),
            total_bonus=float(entry.total_bonus),
            total_compensation=float(entry.total_compensation),
        )
        for entry, rep in rows
    ]


@router.get("/payroll/{pay_period_id}/export", dependencies=[Depends(require_admin)])
def export_payroll_csv(pay_period_id: int, db: Session = Depends(get_db)):
    data = payroll_summary(pay_period_id, db)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["rep_id", "rep_name", "base_pay", "total_bonus", "total_compensation"])
    writer.writeheader()
    writer.writerows([row.model_dump() for row in data])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=payroll_{pay_period_id}.csv"},
    )


@router.get("/reports/conversion", response_model=ConversionReport, dependencies=[Depends(require_admin)])
def conversion_report(db: Session = Depends(get_db)):
    return ConversionReport(**get_conversion_report(db))
