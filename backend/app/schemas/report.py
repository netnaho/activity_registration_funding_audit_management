from datetime import datetime

from pydantic import BaseModel


class ReportRequest(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
