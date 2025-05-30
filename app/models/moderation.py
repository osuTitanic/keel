
from pydantic import BaseModel
from datetime import datetime
from enum import IntEnum

class InfringementAction(IntEnum):
    Restrict = 0
    Silence = 1

class InfringementModel(BaseModel):
    id: int
    user_id: int
    time: datetime
    length: datetime
    action: InfringementAction
    is_permanent: bool
    description: str

class InfringementCreateRequest(BaseModel):
    duration: int
    action: InfringementAction
    description: str
    is_permanent: bool = False

class InfringementUpdateRequest(BaseModel):
    duration: int
    description: str
    is_permanent: bool = False

class NameChangeRequest(BaseModel):
    name: str

class NameHistoryUpdateRequest(BaseModel):
    name: str
    reserved: bool = True

class BadgeUpdateRequest(BaseModel):
    description: str
    icon_url: str
    badge_url: str | None = None
