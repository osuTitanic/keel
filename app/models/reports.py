
from pydantic import BaseModel
from datetime import datetime

class ReportModel(BaseModel):
    id: int
    sender_id: int
    target_id: int
    time: datetime
    reason: str
    resolved: bool
