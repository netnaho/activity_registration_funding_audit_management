from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TransactionType


class FundingTransaction(Base):
    __tablename__ = "funding_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    funding_account_id: Mapped[int] = mapped_column(
        ForeignKey("funding_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type_enum", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    invoice_original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_stored_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
