import pytest

from app.core.exceptions import APIError
from app.models.enums import MaterialStatus


def validate_transition(current: MaterialStatus, target: MaterialStatus):
    allowed = {
        MaterialStatus.PENDING_SUBMISSION: {MaterialStatus.SUBMITTED},
        MaterialStatus.SUBMITTED: {MaterialStatus.NEEDS_CORRECTION},
        MaterialStatus.NEEDS_CORRECTION: {MaterialStatus.PENDING_SUBMISSION},
    }
    if target not in allowed.get(current, set()):
        raise APIError(400, "invalid transition")


def test_valid_pending_to_submitted():
    validate_transition(MaterialStatus.PENDING_SUBMISSION, MaterialStatus.SUBMITTED)


def test_invalid_submitted_to_pending_direct():
    with pytest.raises(APIError):
        validate_transition(MaterialStatus.SUBMITTED, MaterialStatus.PENDING_SUBMISSION)
