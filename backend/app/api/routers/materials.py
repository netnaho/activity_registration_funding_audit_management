from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.db.session import get_db
from app.models.enums import MaterialStatus, UserRole
from app.models.user import User
from app.schemas.material import MaterialStatusUpdateRequest
from app.services.audit_service import write_audit_log
from app.services.material_service import list_registration_materials_for_actor, update_material_version_status, upload_material
from app.storage.local_storage import LocalStorageService


router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.post("/upload")
def upload_material_endpoint(
    registration_id: int = Form(...),
    checklist_item_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.APPLICANT})),
):
    storage = LocalStorageService()
    result = upload_material(
        db,
        registration_id=registration_id,
        checklist_item_id=checklist_item_id,
        file=file,
        actor=current_user,
        storage=storage,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="material_upload",
        target_type="registration",
        target_id=str(registration_id),
        details=f"Uploaded checklist item {checklist_item_id}, version {result['version_number']}",
    )
    return success_response(data=result, msg="Material uploaded")


@router.get("/{registration_id}")
def list_materials(registration_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles({UserRole.APPLICANT, UserRole.REVIEWER, UserRole.SYSTEM_ADMIN}))):
    data = list_registration_materials_for_actor(db, registration_id, current_user)
    return success_response(data={"items": data}, msg="Materials fetched")


@router.patch("/status")
def update_material_status(
    payload: MaterialStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.REVIEWER, UserRole.SYSTEM_ADMIN})),
):
    version = update_material_version_status(
        db,
        material_version_id=payload.material_version_id,
        target_status=MaterialStatus(payload.status),
        actor=current_user,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="material_status_update",
        target_type="material_version",
        target_id=str(version.id),
        details=f"status={version.status.value}",
    )
    return success_response(
        data={
            "material_version_id": version.id,
            "status": version.status.value,
        },
        msg="Material status updated",
    )
