from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.similarity_service import check_similarity


router = APIRouter(prefix="/api/similarity", tags=["similarity"])


@router.get("/check")
def check_similarity_endpoint(
    sha256_hash: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN, UserRole.REVIEWER, UserRole.APPLICANT})),
): 
    result = check_similarity(db, sha256_hash, current_user)
    return success_response(data=result, msg="Similarity check executed")
