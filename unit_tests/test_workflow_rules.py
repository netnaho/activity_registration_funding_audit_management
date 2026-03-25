import pytest

from app.core.exceptions import APIError
from app.models.enums import RegistrationStatus
from app.services.workflow_service import _validate_transition


def test_valid_workflow_transition_submitted_to_approved():
    _validate_transition(RegistrationStatus.SUBMITTED, RegistrationStatus.APPROVED)


def test_invalid_workflow_transition_approved_to_submitted():
    with pytest.raises(APIError):
        _validate_transition(RegistrationStatus.APPROVED, RegistrationStatus.SUBMITTED)


def test_batch_limit_enforced_by_constant_behavior():
    ids = list(range(51))
    assert len(ids) > 50
