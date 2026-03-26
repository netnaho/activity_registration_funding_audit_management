from pydantic import BaseModel, Field


class MaterialUploadMeta(BaseModel):
    registration_id: int
    checklist_item_id: int


class MaterialStatusUpdateRequest(BaseModel):
    material_version_id: int
    status: str = Field(pattern="^(pending_submission|submitted|needs_correction)$")
