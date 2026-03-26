from pydantic import BaseModel, Field


class SecureConfigSetRequest(BaseModel):
    value: str = Field(min_length=1, max_length=4000)
