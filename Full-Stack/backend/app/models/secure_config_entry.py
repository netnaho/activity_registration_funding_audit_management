from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SecureConfigEntry(Base):
    __tablename__ = "secure_config_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    config_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    encrypted_value: Mapped[str] = mapped_column(String(4096), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
