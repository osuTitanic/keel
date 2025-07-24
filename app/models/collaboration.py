
from pydantic import BaseModel
from datetime import datetime

from .beatmap import BeatmapModel
from .user import UserModelCompact

class CollaborationModel(BaseModel):
    user: UserModelCompact
    beatmap: BeatmapModel
    is_beatmap_author: bool
    allow_resource_updates: bool
    created_at: datetime

class CollaborationModelWithoutBeatmap(BaseModel):
    user: UserModelCompact
    is_beatmap_author: bool
    allow_resource_updates: bool
    created_at: datetime

class CollaborationRequestModel(BaseModel):
    user: UserModelCompact
    target: UserModelCompact
    beatmap: BeatmapModel
    created_at: datetime

class CollaborationRequestModelWithoutBeatmap(BaseModel):
    user: UserModelCompact
    target: UserModelCompact
    created_at: datetime

class CollaborationBlacklistModel(BaseModel):
    user: UserModelCompact
    target: UserModelCompact
    created_at: datetime

class CollaborationCreateRequest(BaseModel):
    user_id: int
