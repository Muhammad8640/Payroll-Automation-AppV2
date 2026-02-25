from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin")


class Rep(Base):
    __tablename__ = "reps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_rep_id: Mapped[int | None] = mapped_column(ForeignKey("reps.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assigned_rep = relationship("Rep")


class Status(Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)


class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)
    changed_by_rep_id: Mapped[int | None] = mapped_column(ForeignKey("reps.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    lead = relationship("Lead")
    status = relationship("Status")


class StatusBonusRule(Base):
    __tablename__ = "status_bonus_rules"
    __table_args__ = (UniqueConstraint("status_id", "role_type", name="uq_status_role_bonus"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)
    role_type: Mapped[str] = mapped_column(String(50), nullable=False)
    bonus_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class RepBonusOverride(Base):
    __tablename__ = "rep_bonus_overrides"
    __table_args__ = (UniqueConstraint("rep_id", "status_id", name="uq_rep_status_override"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rep_id: Mapped[int] = mapped_column(ForeignKey("reps.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)
    bonus_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class PayPeriod(Base):
    __tablename__ = "pay_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pay_period_id: Mapped[int] = mapped_column(ForeignKey("pay_periods.id"), nullable=False)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PayrollEntry(Base):
    __tablename__ = "payroll_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payroll_run_id: Mapped[int] = mapped_column(ForeignKey("payroll_runs.id"), nullable=False)
    rep_id: Mapped[int] = mapped_column(ForeignKey("reps.id"), nullable=False)
    base_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_bonus: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_compensation: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
