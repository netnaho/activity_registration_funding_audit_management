from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, UserMeResponse
from app.services.audit_service import write_audit_log
from app.services.auth_service import authenticate_user, generate_token_for_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, error = authenticate_user(
        db,
        username=payload.username,
        password=payload.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if error or user is None:
        return JSONResponse(status_code=401, content={"code": 401, "msg": error or "Unauthorized", "data": None})

    token = generate_token_for_user(user)
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="login_success",
        target_type="user",
        target_id=str(user.id),
        details="User logged in",
    )
    return JSONResponse(
        status_code=200,
        content=success_response(data={"access_token": token, "token_type": "bearer"}, msg="Login success"),
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    data = UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.value,
    ).model_dump()
    return success_response(data=data, msg="Profile fetched")
