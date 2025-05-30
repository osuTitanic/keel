
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

class LoginModel(BaseModel):
    user_id: int
    time: datetime
    ip: str
    version: str

class UserMetadataModel(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    is_bot: bool
    country: str
    activated: bool
    restricted: bool
    discord_id: int | None
    userpage: str | None
    signature: str | None
    title: str | None
    banner: str | None
    website: str | None
    discord: str | None
    twitter: str | None
    location: str | None
    interests: str | None

class UserMetadataUpdateRequest(BaseModel):
    email: str
    country: str
    is_bot: bool = False
    activated: bool = True
    discord_id: int | None = None
    userpage: str | None = None
    signature: str | None = None
    title: str | None = None
    banner: str | None = None
    website: str | None = None
    discord: str | None = None
    twitter: str | None = None
    location: str | None = None
    interests: str | None = None
