from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.responses import success_response
from app.models.user import User


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(current_user: User = Depends(get_current_user)) -> dict:
    return success_response(
        data={"welcome": f"Welcome, {current_user.full_name}", "role": current_user.role.value},
        msg="Dashboard summary",
    )
