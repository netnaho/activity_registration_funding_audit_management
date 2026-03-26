from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FundingAccount(Base):
    __tablename__ = "funding_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    budget_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
