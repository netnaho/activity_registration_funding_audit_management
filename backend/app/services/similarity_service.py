from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material_version import MaterialVersion
from app.models.registration_material_submission import RegistrationMaterialSubmission
from app.models.registration_form import RegistrationForm
from app.models.user import User


def check_similarity(db: Session, sha256_hash: str, actor: User) -> dict:
    if not settings.similarity_check_enabled:
        return {
            "enabled": False,
            "status": "disabled",
            "message": "Similarity/duplicate extension is disabled by configuration",
            "matches": [],
        }

    query = select(MaterialVersion).where(MaterialVersion.sha256_hash == sha256_hash)
    if actor.role.value == "applicant":
        query = (
            query.join(RegistrationMaterialSubmission, RegistrationMaterialSubmission.id == MaterialVersion.submission_id)
            .join(RegistrationForm, RegistrationForm.id == RegistrationMaterialSubmission.registration_form_id)
            .where(RegistrationForm.applicant_id == actor.id)
        )

    matches = db.scalars(query).all()
    return {
        "enabled": True,
        "status": "ok",
        "matches": [
            {
                "material_version_id": m.id,
                "submission_id": m.submission_id,
                "sha256_hash": m.sha256_hash,
            }
            for m in matches
        ],
    }
