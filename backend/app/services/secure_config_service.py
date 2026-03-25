from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.secure_config_entry import SecureConfigEntry
from app.security.config_crypto import decrypt_config_value, encrypt_config_value


def set_secure_config(db: Session, *, key: str, value: str, updated_by: int) -> SecureConfigEntry:
    existing = db.scalar(select(SecureConfigEntry).where(SecureConfigEntry.config_key == key))
    encrypted = encrypt_config_value(value)
    if existing:
        existing.encrypted_value = encrypted
        existing.updated_by = updated_by
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    record = SecureConfigEntry(
        config_key=key,
        encrypted_value=encrypted,
        updated_by=updated_by,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_secure_config_metadata(db: Session) -> list[dict]:
    rows = db.scalars(select(SecureConfigEntry).order_by(SecureConfigEntry.config_key.asc())).all()
    return [
        {
            "key": row.config_key,
            "is_set": True,
            "updated_by": row.updated_by,
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
    ]


def get_secure_config_for_internal_use(db: Session, key: str) -> str | None:
    row = db.scalar(select(SecureConfigEntry).where(SecureConfigEntry.config_key == key))
    if not row:
        return None
    return decrypt_config_value(row.encrypted_value)
