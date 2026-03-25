from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import APIError
from app.models.enums import MaterialStatus
from app.models.material_checklist import MaterialChecklistItem
from app.models.material_version import MaterialVersion
from app.models.registration_form import RegistrationForm
from app.models.registration_material_submission import RegistrationMaterialSubmission
from app.models.user import User
from app.services.registration_service import assert_registration_actor_access
from app.services.registration_service import ensure_registration_upload_limit, maybe_lock_registration
from app.storage.local_storage import LocalStorageService

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 20 * 1024 * 1024

MATERIAL_ALLOWED_TRANSITIONS: dict[MaterialStatus, set[MaterialStatus]] = {
    MaterialStatus.PENDING_SUBMISSION: {MaterialStatus.SUBMITTED},
    MaterialStatus.SUBMITTED: {MaterialStatus.NEEDS_CORRECTION},
    MaterialStatus.NEEDS_CORRECTION: {MaterialStatus.PENDING_SUBMISSION},
}


def _ensure_registration_access(registration: RegistrationForm, user: User) -> None:
    if user.id != registration.applicant_id:
        raise APIError(403, "You can only manage your own registration materials")


def _check_file_constraints(filename: str, size: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise APIError(400, "Only PDF/JPG/PNG files are allowed")
    if size > MAX_FILE_SIZE:
        raise APIError(400, "Single file must be <= 20MB")


def _find_or_create_submission(db: Session, registration_id: int, checklist_item_id: int) -> RegistrationMaterialSubmission:
    submission = db.scalar(
        select(RegistrationMaterialSubmission).where(
            RegistrationMaterialSubmission.registration_form_id == registration_id,
            RegistrationMaterialSubmission.checklist_item_id == checklist_item_id,
        )
    )
    if submission:
        return submission
    submission = RegistrationMaterialSubmission(
        registration_form_id=registration_id,
        checklist_item_id=checklist_item_id,
        total_size_bytes=0,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def _next_version_number(db: Session, submission_id: int) -> int:
    count = db.scalar(select(func.count(MaterialVersion.id)).where(MaterialVersion.submission_id == submission_id))
    count_int = int(count or 0)
    if count_int >= 3:
        raise APIError(400, "Maximum 3 versions are allowed for one material")
    return count_int + 1


def upload_material(
    db: Session,
    *,
    registration_id: int,
    checklist_item_id: int,
    file: UploadFile,
    actor: User,
    storage: LocalStorageService,
) -> dict:
    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == registration_id))
    if not registration:
        raise APIError(404, "Registration not found")
    _ensure_registration_access(registration, actor)

    maybe_lock_registration(registration)
    if registration.is_locked:
        db.commit()
        raise APIError(400, "Registration materials are locked after deadline")

    checklist_item = db.scalar(select(MaterialChecklistItem).where(MaterialChecklistItem.id == checklist_item_id))
    if not checklist_item:
        raise APIError(404, "Checklist item not found")

    payload = file.file.read()
    file_size = len(payload)
    _check_file_constraints(file.filename or "", file_size)
    if file_size > checklist_item.max_size_mb * 1024 * 1024:
        raise APIError(400, f"Checklist item file must be <= {checklist_item.max_size_mb}MB")

    ensure_registration_upload_limit(db, registration_id, file_size)

    store_result = storage.save_bytes("materials", file.filename or "file", payload)
    duplicate = db.scalar(select(MaterialVersion.id).where(MaterialVersion.sha256_hash == store_result["sha256"])) is not None

    submission = _find_or_create_submission(db, registration_id, checklist_item_id)
    if submission.is_locked:
        raise APIError(400, "Material is locked")

    version_number = _next_version_number(db, submission.id)
    version = MaterialVersion(
        submission_id=submission.id,
        version_number=version_number,
        status=MaterialStatus.PENDING_SUBMISSION,
        original_filename=file.filename or "file",
        stored_filename=str(store_result["stored_filename"]),
        file_extension=Path(file.filename or "file").suffix.lower(),
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        sha256_hash=str(store_result["sha256"]),
        uploaded_by=actor.id,
        uploaded_at=datetime.now(timezone.utc),
    )
    submission.total_size_bytes += file_size
    db.add(version)
    db.commit()
    db.refresh(version)
    return {
        "material_version_id": version.id,
        "version_number": version.version_number,
        "status": version.status.value,
        "sha256": version.sha256_hash,
        "duplicate_detected": duplicate,
    }


def enforce_material_access(registration: RegistrationForm, actor: User) -> None:
    assert_registration_actor_access(registration=registration, actor=actor, allow_reviewer_admin=True)


def list_registration_materials_for_actor(db: Session, registration_id: int, actor: User) -> list[dict]:
    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == registration_id))
    if not registration:
        raise APIError(404, "Registration not found")
    enforce_material_access(registration, actor)
    return list_registration_materials(db, registration_id)


def update_material_version_status(
    db: Session,
    *,
    material_version_id: int,
    target_status: MaterialStatus,
    actor: User,
) -> MaterialVersion:
    version = db.scalar(select(MaterialVersion).where(MaterialVersion.id == material_version_id))
    if not version:
        raise APIError(404, "Material version not found")

    submission = db.scalar(
        select(RegistrationMaterialSubmission).where(RegistrationMaterialSubmission.id == version.submission_id)
    )
    if not submission:
        raise APIError(404, "Material submission not found")

    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == submission.registration_form_id))
    if not registration:
        raise APIError(404, "Registration not found")

    if actor.role.value == "applicant":
        if registration.applicant_id != actor.id:
            raise APIError(403, "Forbidden resource access")
    elif actor.role.value not in {"reviewer", "system_admin"}:
        raise APIError(403, "Forbidden")

    current_status = version.status
    allowed = MATERIAL_ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise APIError(400, f"Invalid material status transition from {current_status.value} to {target_status.value}")

    version.status = target_status
    db.commit()
    db.refresh(version)
    return version


def mark_latest_versions_needs_correction(db: Session, registration_id: int) -> int:
    submissions = db.scalars(
        select(RegistrationMaterialSubmission).where(RegistrationMaterialSubmission.registration_form_id == registration_id)
    ).all()
    changed = 0
    for submission in submissions:
        latest = db.scalar(
            select(MaterialVersion)
            .where(MaterialVersion.submission_id == submission.id)
            .order_by(MaterialVersion.version_number.desc())
            .limit(1)
        )
        if latest and latest.status == MaterialStatus.SUBMITTED:
            latest.status = MaterialStatus.NEEDS_CORRECTION
            changed += 1
    if changed:
        db.commit()
    return changed


def mark_pending_versions_submitted(db: Session, registration_id: int) -> int:
    versions = db.scalars(
        select(MaterialVersion)
        .join(RegistrationMaterialSubmission, RegistrationMaterialSubmission.id == MaterialVersion.submission_id)
        .where(
            RegistrationMaterialSubmission.registration_form_id == registration_id,
            MaterialVersion.status == MaterialStatus.PENDING_SUBMISSION,
        )
    ).all()
    for version in versions:
        version.status = MaterialStatus.SUBMITTED
    if versions:
        db.commit()
    return len(versions)


def list_registration_materials(db: Session, registration_id: int) -> list[dict]:
    rows = db.execute(
        select(
            RegistrationMaterialSubmission.id,
            RegistrationMaterialSubmission.checklist_item_id,
            RegistrationMaterialSubmission.total_size_bytes,
            MaterialVersion.id,
            MaterialVersion.version_number,
            MaterialVersion.status,
            MaterialVersion.original_filename,
            MaterialVersion.file_size_bytes,
            MaterialVersion.sha256_hash,
            MaterialVersion.uploaded_at,
        )
        .join(MaterialVersion, MaterialVersion.submission_id == RegistrationMaterialSubmission.id)
        .where(RegistrationMaterialSubmission.registration_form_id == registration_id)
        .order_by(RegistrationMaterialSubmission.id, MaterialVersion.version_number)
    ).all()

    result: dict[int, dict] = {}
    for row in rows:
        submission_id = row[0]
        if submission_id not in result:
            result[submission_id] = {
                "submission_id": submission_id,
                "checklist_item_id": row[1],
                "total_size_bytes": int(row[2]),
                "versions": [],
            }
        result[submission_id]["versions"].append(
            {
                "material_version_id": row[3],
                "version_number": row[4],
                "status": row[5].value if hasattr(row[5], "value") else str(row[5]),
                "original_filename": row[6],
                "file_size_bytes": int(row[7]),
                "sha256_hash": row[8],
                "uploaded_at": row[9].isoformat() if row[9] else None,
            }
        )
    return list(result.values())
