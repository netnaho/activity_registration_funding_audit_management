from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.backup_service import create_local_backup, list_backups, recover_backup


router = APIRouter(prefix="/api/backups", tags=["backups"])


@router.post("/create")
def create_backup_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    record = create_local_backup(db, triggered_by=current_user.id)
    return success_response(
        data={
            "id": record.id,
            "file_path": record.file_path,
            "status": record.status,
        },
        msg="Backup created",
    )


@router.get("")
def list_backup_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    records = list_backups(db)
    return success_response(
        data={
            "items": [
                {
                    "id": r.id,
                    "backup_type": r.backup_type,
                    "file_path": r.file_path,
                    "status": r.status,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
        },
        msg="Backups listed",
    )


@router.post("/{backup_id}/recover")
def recover_backup_endpoint(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    message = recover_backup(db, backup_id)
    return success_response(data={"message": message}, msg="Backup recovered")
