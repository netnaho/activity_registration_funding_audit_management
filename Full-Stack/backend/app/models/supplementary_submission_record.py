from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SupplementarySubmissionRecord(Base):
    __tablename__ = "supplementary_submission_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_form_id: Mapped[int] = mapped_column(
        ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
