from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions import APIError
from app.models.enums import MaterialStatus, RegistrationStatus, UserRole
from app.models.material_checklist import MaterialChecklistItem
from app.models.material_version import MaterialVersion
from app.models.registration_form import RegistrationForm
from app.models.registration_material_submission import RegistrationMaterialSubmission
from app.models.review_workflow_record import ReviewWorkflowRecord
from app.services.material_service import _next_version_number
from app.services.registration_service import create_supplementary_window, ensure_registration_upload_limit, maybe_lock_registration


def test_aggregate_upload_limit_200mb_enforced(db_session, user_factory):
    applicant = user_factory("applicant_limit", UserRole.APPLICANT)
    reg = RegistrationForm(
        applicant_id=applicant.id,
        title="Limit Test",
        description="limit test",
        contact_phone="5551119999",
        id_number="IDLIM1",
        deadline_at=datetime.now(timezone.utc) + timedelta(days=1),
        status=RegistrationStatus.DRAFT,
    )
    db_session.add(reg)
    db_session.commit()
    db_session.refresh(reg)

    submission = RegistrationMaterialSubmission(
        registration_form_id=reg.id,
        checklist_item_id=1,
        total_size_bytes=200 * 1024 * 1024,
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    mv = MaterialVersion(
        submission_id=submission.id,
        version_number=1,
        status=MaterialStatus.SUBMITTED,
        original_filename="x.pdf",
        stored_filename="x1.pdf",
        file_extension=".pdf",
        content_type="application/pdf",
        file_size_bytes=200 * 1024 * 1024,
        sha256_hash="h1",
        uploaded_by=applicant.id,
    )
    db_session.add(mv)
    db_session.commit()

    with pytest.raises(APIError) as exc:
        ensure_registration_upload_limit(db_session, reg.id, 1)
    assert exc.value.status_code == 400


def test_max_three_versions_enforced(db_session, user_factory):
    applicant = user_factory("applicant_vmax", UserRole.APPLICANT)
    reg = RegistrationForm(
        applicant_id=applicant.id,
        title="Version Test",
        description="version test",
        contact_phone="5551118888",
        id_number="IDVMAX",
        deadline_at=datetime.now(timezone.utc) + timedelta(days=1),
        status=RegistrationStatus.DRAFT,
    )
    db_session.add(reg)
    db_session.commit()
    db_session.refresh(reg)

    submission = RegistrationMaterialSubmission(registration_form_id=reg.id, checklist_item_id=1, total_size_bytes=100)
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    for idx in range(1, 4):
        db_session.add(
            MaterialVersion(
                submission_id=submission.id,
                version_number=idx,
                status=MaterialStatus.SUBMITTED,
                original_filename=f"v{idx}.pdf",
                stored_filename=f"v{idx}.stored.pdf",
                file_extension=".pdf",
                content_type="application/pdf",
                file_size_bytes=10,
                sha256_hash=f"h{idx}",
                uploaded_by=applicant.id,
            )
        )
    db_session.commit()

    with pytest.raises(APIError) as exc:
        _next_version_number(db_session, submission.id)
    assert exc.value.status_code == 400


def test_supplementary_window_expires_after_72_hours(db_session, user_factory):
    applicant = user_factory("applicant_sup_exp", UserRole.APPLICANT)
    reviewer = user_factory("reviewer_sup_exp", UserRole.REVIEWER)

    reg = RegistrationForm(
        applicant_id=applicant.id,
        title="Supplementary Expiry",
        description="supplementary expiry",
        contact_phone="5551117777",
        id_number="IDSUP72",
        deadline_at=datetime.now(timezone.utc) + timedelta(days=1),
        status=RegistrationStatus.SUPPLEMENTED,
        submitted_at=datetime.now(timezone.utc) - timedelta(days=4),
    )
    db_session.add(reg)
    db_session.commit()
    db_session.refresh(reg)

    trigger = ReviewWorkflowRecord(
        registration_form_id=reg.id,
        reviewer_id=reviewer.id,
        from_status=RegistrationStatus.SUBMITTED,
        to_status=RegistrationStatus.SUPPLEMENTED,
        comment="needs correction",
        created_at=datetime.now(timezone.utc) - timedelta(hours=73),
    )
    db_session.add(trigger)
    db_session.commit()

    with pytest.raises(APIError) as exc:
        create_supplementary_window(db_session, reg, applicant, "too late")
    assert exc.value.status_code == 400
    assert "72 hours" in exc.value.message


def test_deadline_auto_lock_sets_registration_locked():
    reg = RegistrationForm(
        applicant_id=1,
        title="Deadline Lock",
        description="deadline lock",
        contact_phone="5551116666",
        id_number="IDLOCK",
        deadline_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        status=RegistrationStatus.DRAFT,
        is_locked=False,
    )
    changed = maybe_lock_registration(reg)
    assert changed is True
    assert reg.is_locked is True
