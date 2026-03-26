from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.logging.logger import app_logger, log_info, log_warning
from app.models.login_attempt_log import LoginAttemptLog
from app.models.user import User

LOCK_WINDOW_MINUTES = 5
LOCK_THRESHOLD = 10
LOCK_DURATION_MINUTES = 30

logger = app_logger("app.auth")


def _is_locked(user: User) -> bool:
    if not user.locked_until:
        return False
    return user.locked_until > datetime.now(timezone.utc)


def authenticate_user(
    db: Session,
    *,
    username: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[User | None, str | None]:
    user = db.scalar(select(User).where(User.username == username))

    if not user:
        log_warning(
            logger,
            event="login_failed_unknown_user",
            category="security",
            context={"username": username, "ip_address": ip_address},
        )
        db.add(
            LoginAttemptLog(
                username=username,
                user_id=None,
                success=False,
                reason="invalid_credentials",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        db.commit()
        return None, "Invalid username or password"

    if _is_locked(user):
        log_warning(
            logger,
            event="login_blocked_locked_account",
            category="security",
            context={"username": username, "user_id": user.id, "ip_address": ip_address},
        )
        db.add(
            LoginAttemptLog(
                username=username,
                user_id=user.id,
                success=False,
                reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        db.commit()
        return None, "Account is locked. Try again later"

    if not verify_password(password, user.password_hash):
        now = datetime.now(timezone.utc)
        if user.first_failed_attempt_at is None or (now - user.first_failed_attempt_at) > timedelta(minutes=LOCK_WINDOW_MINUTES):
            user.first_failed_attempt_at = now
            user.failed_attempt_count = 1
        else:
            user.failed_attempt_count += 1

        if user.failed_attempt_count >= LOCK_THRESHOLD:
            user.locked_until = now + timedelta(minutes=LOCK_DURATION_MINUTES)
            log_warning(
                logger,
                event="account_lockout_triggered",
                category="security",
                context={"username": username, "user_id": user.id, "failed_attempt_count": user.failed_attempt_count},
            )

        db.add(
            LoginAttemptLog(
                username=username,
                user_id=user.id,
                success=False,
                reason="invalid_credentials",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        db.commit()
        return None, "Invalid username or password"

    user.failed_attempt_count = 0
    user.first_failed_attempt_at = None
    user.locked_until = None
    log_info(
        logger,
        event="login_success",
        category="security",
        context={"username": username, "user_id": user.id, "ip_address": ip_address},
    )
    db.add(
        LoginAttemptLog(
            username=username,
            user_id=user.id,
            success=True,
            reason="success",
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )
    db.commit()
    return user, None


def generate_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id), role=user.role.value)
