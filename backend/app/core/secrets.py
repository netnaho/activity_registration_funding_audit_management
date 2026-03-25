from __future__ import annotations

import secrets
from pathlib import Path

from app.core.config import settings


_JWT_SECRET_CACHE: str | None = None
_WEAK_JWT_VALUES = {"", "change-me-in-production", "changeme", "default", "secret"}


def _is_weak_secret(secret_value: str) -> bool:
    lowered = secret_value.strip().lower()
    return lowered in _WEAK_JWT_VALUES or len(secret_value.strip()) < 32


def _jwt_secret_path() -> Path:
    security_dir = Path(settings.security_dir)
    security_dir.mkdir(parents=True, exist_ok=True)
    return security_dir / "jwt_secret.key"


def get_jwt_secret_key() -> str:
    global _JWT_SECRET_CACHE

    if _JWT_SECRET_CACHE:
        return _JWT_SECRET_CACHE

    provided = (settings.jwt_secret_key or "").strip()
    if provided:
        if _is_weak_secret(provided):
            raise RuntimeError("JWT secret is weak. Provide at least 32 high-entropy characters.")
        _JWT_SECRET_CACHE = provided
        return _JWT_SECRET_CACHE

    secret_file = _jwt_secret_path()
    if secret_file.exists():
        loaded = secret_file.read_text(encoding="utf-8").strip()
        if loaded and not _is_weak_secret(loaded):
            _JWT_SECRET_CACHE = loaded
            return _JWT_SECRET_CACHE

    generated = secrets.token_urlsafe(64)
    secret_file.write_text(generated, encoding="utf-8")
    secret_file.chmod(0o600)
    _JWT_SECRET_CACHE = generated
    return _JWT_SECRET_CACHE
