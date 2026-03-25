from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

from app.core.config import settings


def _key_file_path() -> Path:
    security_dir = Path(settings.security_dir)
    security_dir.mkdir(parents=True, exist_ok=True)
    return security_dir / "config_encryption.key"


def load_or_create_key() -> bytes:
    if settings.config_encryption_key:
        return settings.config_encryption_key.encode("utf-8")

    key_file = _key_file_path()
    if key_file.exists():
        return key_file.read_bytes().strip()

    key = Fernet.generate_key()
    key_file.write_bytes(key)
    key_file.chmod(0o600)
    return key


def encrypt_config_value(value: str) -> str:
    f = Fernet(load_or_create_key())
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_config_value(cipher_text: str) -> str:
    f = Fernet(load_or_create_key())
    return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
