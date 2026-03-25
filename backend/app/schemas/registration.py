from datetime import datetime

from pydantic import BaseModel, Field


class RegistrationCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=4000)
    contact_phone: str = Field(min_length=6, max_length=32)
    id_number: str = Field(min_length=4, max_length=32)
    deadline_at: datetime


class RegistrationSubmitRequest(BaseModel):
    registration_id: int


class SupplementaryRequest(BaseModel):
    registration_id: int
    reason: str = Field(min_length=5, max_length=500)
