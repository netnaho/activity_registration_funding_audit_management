from datetime import datetime, timedelta, timezone


class DummyUser:
    def __init__(self):
        self.failed_attempt_count = 0
        self.first_failed_attempt_at = None
        self.locked_until = None


LOCK_WINDOW_MINUTES = 5
LOCK_THRESHOLD = 10
LOCK_DURATION_MINUTES = 30


def apply_failed_login(user: DummyUser, now: datetime) -> None:
    if user.first_failed_attempt_at is None or (now - user.first_failed_attempt_at) > timedelta(minutes=LOCK_WINDOW_MINUTES):
        user.first_failed_attempt_at = now
        user.failed_attempt_count = 1
    else:
        user.failed_attempt_count += 1

    if user.failed_attempt_count >= LOCK_THRESHOLD:
        user.locked_until = now + timedelta(minutes=LOCK_DURATION_MINUTES)


def test_lockout_after_10_failures_within_window():
    user = DummyUser()
    base = datetime.now(timezone.utc)
    for idx in range(10):
        apply_failed_login(user, base + timedelta(seconds=idx))
    assert user.failed_attempt_count == 10
    assert user.locked_until is not None
    assert user.locked_until > base


def test_failure_counter_resets_outside_window():
    user = DummyUser()
    base = datetime.now(timezone.utc)
    apply_failed_login(user, base)
    apply_failed_login(user, base + timedelta(minutes=6))
    assert user.failed_attempt_count == 1
