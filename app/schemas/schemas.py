from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "admin"


class RepBase(BaseModel):
    name: str
    role_type: str
    base_pay: float
    is_active: bool = True


class RepCreate(RepBase):
    pass


class RepOut(RepBase):
    id: int

    class Config:
        from_attributes = True


class LeadCreate(BaseModel):
    title: str
    assigned_rep_id: int | None = None


class LeadOut(BaseModel):
    id: int
    title: str
    assigned_rep_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class StatusCreate(BaseModel):
    code: str
    label: str


class StatusOut(BaseModel):
    id: int
    code: str
    label: str

    class Config:
        from_attributes = True


class LeadStatusUpdate(BaseModel):
    lead_id: int
    status_id: int
    changed_by_rep_id: int | None = None


class LeadStatusHistoryOut(BaseModel):
    id: int
    lead_id: int
    status_id: int
    changed_by_rep_id: int | None
    changed_at: datetime

    class Config:
        from_attributes = True


class StatusBonusRuleCreate(BaseModel):
    status_id: int
    role_type: str
    bonus_amount: float


class RepBonusOverrideCreate(BaseModel):
    rep_id: int
    status_id: int
    bonus_amount: float


class PayPeriodCreate(BaseModel):
    start_date: date
    end_date: date
    locked: bool = False


class PayPeriodOut(PayPeriodCreate):
    id: int

    class Config:
        from_attributes = True


class PayrollEntryOut(BaseModel):
    rep_id: int
    rep_name: str
    base_pay: float
    total_bonus: float
    total_compensation: float


class ConversionReport(BaseModel):
    total_leads: int
    won_leads: int
    conversion_rate: float
