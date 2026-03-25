from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import RegistrationStatus


class ReviewWorkflowRecord(Base):
    __tablename__ = "review_workflow_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_form_id: Mapped[int] = mapped_column(
        ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    from_status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status_enum", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    to_status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status_enum", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    batch_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
