
from app.common.constants import UserActivity
from pydantic import BaseModel
from datetime import datetime

class ActivityModel(BaseModel):
    id: int
    user_id: int
    mode: int
    time: datetime
    type: UserActivity
    data: dict
