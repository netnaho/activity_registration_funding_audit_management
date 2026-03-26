from app.core.secrets import _is_weak_secret


def test_weak_default_secret_detected():
    assert _is_weak_secret("change-me-in-production") is True


def test_short_secret_detected():
    assert _is_weak_secret("abc123") is True


def test_strong_secret_accepted():
    strong = "x" * 64
    assert _is_weak_secret(strong) is False
