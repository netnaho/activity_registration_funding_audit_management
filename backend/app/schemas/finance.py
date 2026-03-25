from datetime import datetime

from pydantic import BaseModel, Field


class FundingAccountCreateRequest(BaseModel):
    account_name: str = Field(min_length=2, max_length=150)
    category: str = Field(min_length=2, max_length=64)
    period: str = Field(min_length=2, max_length=32)
    budget_amount: float = Field(gt=0)


class FundingTransactionCreateRequest(BaseModel):
    funding_account_id: int
    transaction_type: str = Field(pattern="^(income|expense)$")
    amount: float = Field(gt=0)
    transaction_time: datetime
    category: str = Field(min_length=2, max_length=64)
    note: str | None = Field(default=None, max_length=500)
    overspend_confirmed: bool = False
