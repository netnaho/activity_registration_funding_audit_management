from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.core.exceptions import APIError
from app.db.session import get_db
from app.models.collection_whitelist_policy import CollectionWhitelistPolicy
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.secure_config import SecureConfigSetRequest
from app.services.secure_config_service import list_secure_config_metadata, set_secure_config


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/settings")
def admin_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    policies = db.scalars(select(CollectionWhitelistPolicy)).all()
    return success_response(
        data={
            "backup": {"enabled": True},
            "whitelist_policies": [
                {
                    "id": p.id,
                    "policy_name": p.policy_name,
                    "scope_rule": p.scope_rule,
                    "is_active": p.is_active,
                }
                for p in policies
            ],
        },
        msg="Admin settings",
    )


@router.post("/whitelist-policies")
def create_whitelist_policy(
    policy_name: str,
    scope_rule: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    record = CollectionWhitelistPolicy(policy_name=policy_name, scope_rule=scope_rule, is_active=True)
    db.add(record)
    db.commit()
    db.refresh(record)
    return success_response(
        data={"id": record.id, "policy_name": record.policy_name, "scope_rule": record.scope_rule, "is_active": True},
        msg="Whitelist policy created",
    )


@router.post("/unlock-user")
def unlock_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    target = db.scalar(select(User).where(User.username == username))
    if not target:
        raise APIError(404, "User not found")
    target.failed_attempt_count = 0
    target.first_failed_attempt_at = None
    target.locked_until = None
    db.commit()
    return success_response(data={"username": target.username, "unlocked": True}, msg="User unlocked")


@router.put("/secure-config/{config_key}")
def set_secure_config_endpoint(
    config_key: str,
    payload: SecureConfigSetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    record = set_secure_config(db, key=config_key, value=payload.value, updated_by=current_user.id)
    return success_response(
        data={
            "key": record.config_key,
            "is_set": True,
            "updated_by": record.updated_by,
            "updated_at": record.updated_at.isoformat(),
        },
        msg="Secure configuration updated",
    )


@router.get("/secure-config")
def list_secure_config_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    return success_response(data={"items": list_secure_config_metadata(db)}, msg="Secure config metadata")
