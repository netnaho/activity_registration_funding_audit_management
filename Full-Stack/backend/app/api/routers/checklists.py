from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.material_checklist import MaterialChecklist, MaterialChecklistItem
from app.models.user import User


router = APIRouter(prefix="/api/checklists", tags=["checklists"])


@router.get("")
def list_checklists(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles({UserRole.APPLICANT, UserRole.REVIEWER, UserRole.SYSTEM_ADMIN, UserRole.FINANCIAL_ADMIN})
    ),
):
    checklists = db.scalars(select(MaterialChecklist).where(MaterialChecklist.is_active.is_(True))).all()
    result = []
    for checklist in checklists:
        items = db.scalars(select(MaterialChecklistItem).where(MaterialChecklistItem.checklist_id == checklist.id)).all()
        result.append(
            {
                "id": checklist.id,
                "name": checklist.name,
                "description": checklist.description,
                "items": [
                    {
                        "id": item.id,
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "required": item.required,
                        "max_size_mb": item.max_size_mb,
                    }
                    for item in items
                ],
            }
        )
    return success_response(data={"items": result}, msg="Checklist list")
