from fastapi import APIRouter

from app.api.responses import success_response


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    return success_response(data={"status": "healthy"}, msg="Service is healthy")
