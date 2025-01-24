
from pydantic import BaseModel
from datetime import datetime
from .user import UserModel

class MessageModel(BaseModel):
    id: int
    sender: UserModel | None
    message: str
    time: datetime

class PrivateMessageModel(BaseModel):
    id: int
    message: str
    time: datetime
    sender_id: int
    target_id: int

class PrivateMessageSelectionEntry(BaseModel):
    user: UserModel
    last_message: PrivateMessageModel
