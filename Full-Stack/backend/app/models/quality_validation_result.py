from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QualityValidationResult(Base):
    __tablename__ = "quality_validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_form_id: Mapped[int] = mapped_column(
        ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approval_rate: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=0)
    correction_rate: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=0)
    overspending_rate: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
