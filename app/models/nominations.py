
from app.models.user import UserModelCompact
from pydantic import BaseModel
from datetime import datetime

class NominationModel(BaseModel):
    set_id: int
    user_id: int
    time: datetime
    user: UserModelCompact
