
from pydantic import BaseModel
from datetime import datetime
from .user import UserModel

class MessageModel(BaseModel):
    id: int
    sender: UserModel | None
    message: str
    time: datetime
