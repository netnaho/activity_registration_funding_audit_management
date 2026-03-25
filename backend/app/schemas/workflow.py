from pydantic import BaseModel, Field


class WorkflowTransitionRequest(BaseModel):
    registration_id: int
    target_status: str = Field(pattern="^(submitted|supplemented|approved|rejected|canceled|promoted_from_waitlist)$")
    comment: str = Field(min_length=2, max_length=1000)


class BatchWorkflowTransitionRequest(BaseModel):
    registration_ids: list[int] = Field(min_length=1, max_length=50)
    target_status: str = Field(pattern="^(approved|rejected|canceled|promoted_from_waitlist|supplemented)$")
    comment: str = Field(min_length=2, max_length=1000)
