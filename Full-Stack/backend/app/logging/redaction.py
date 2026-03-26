from __future__ import annotations

from collections.abc import Mapping


SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "id_number",
    "contact_phone",
    "phone",
    "email",
    "secret",
    "api_key",
}


def redact_value(value: object, mask: str = "***REDACTED***") -> object:
    if isinstance(value, Mapping):
        return redact_mapping(value, mask=mask)
    if isinstance(value, list):
        return [redact_value(item, mask=mask) for item in value]
    return value


def redact_mapping(data: Mapping[str, object], mask: str = "***REDACTED***") -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            redacted[key] = mask
        else:
            redacted[key] = redact_value(value, mask=mask)
    return redacted
