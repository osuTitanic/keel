
from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime

from .beatmapset import BeatmapsetModel
from .user import UserModelCompact

class FavouriteModel(BaseModel):
    user: UserModelCompact
    beatmapset: BeatmapsetModel
    created_at: datetime

class FavouriteCreateRequest(BaseModel):
    set_id: int
