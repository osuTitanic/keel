
from app.common.constants import NotificationType
from pydantic import BaseModel
from datetime import datetime

class NotificationModel(BaseModel):
    id: int
    type: NotificationType
    header: str
    content: str
    link: str | None
    read: bool
    time: datetime
