from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=80)
    expense_date: date
    notes: str | None = None

class ExpenseUpdate(BaseModel):
    title: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = None
    expense_date: date | None = None
    notes: str | None = None

class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    amount: Decimal
    category: str
    expense_date: date
    notes: str | None
    created_at: datetime
