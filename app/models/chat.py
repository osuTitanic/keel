
from pydantic import BaseModel, field_validator
from datetime import datetime
from .user import UserModelCompact

class ChannelModel(BaseModel):
    name: str
    topic: str

class MessageModel(BaseModel):
    id: int
    sender: UserModelCompact | None
    sender_name: str
    message: str
    time: datetime

class PrivateMessageModel(BaseModel):
    id: int
    message: str
    time: datetime
    sender_id: int
    target_id: int
    read: bool

class PrivateMessageSelectionEntry(BaseModel):
    user: UserModelCompact
    last_message: PrivateMessageModel

class MessagePostRequest(BaseModel):
    message: str

    @field_validator('message')
    def truncate_message(cls, value: str) -> str:
        if len(value) < 512:
            return value

        # Truncate message to fit database limits
        return value[:495] + '... (truncated)'
