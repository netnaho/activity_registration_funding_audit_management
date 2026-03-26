from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegistrationMaterialSubmission(Base):
    __tablename__ = "registration_material_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_form_id: Mapped[int] = mapped_column(
        ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checklist_item_id: Mapped[int] = mapped_column(
        ForeignKey("material_checklist_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
