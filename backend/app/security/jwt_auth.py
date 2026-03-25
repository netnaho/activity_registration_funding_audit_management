from jose import JWTError, jwt

from app.core.config import settings
from app.core.secrets import get_jwt_secret_key


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_jwt_secret_key(), algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
