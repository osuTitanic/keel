
from pydantic import BaseModel
from datetime import datetime
from typing import List

from .user import UserModelCompact
from .beatmapset import BeatmapsetModel

class BeatmapPackEntryModel(BaseModel):
    beatmapset: BeatmapsetModel
    created_at: datetime

class BeatmapPackModel(BaseModel):
    id: int
    name: str
    category: str
    description: str
    download_link: str
    creator: UserModelCompact
    created_at: datetime
    updated_at: datetime

class BeatmapPackWithEntriesModel(BaseModel):
    id: int
    name: str
    category: str
    description: str
    download_link: str
    creator: UserModelCompact
    created_at: datetime
    updated_at: datetime
    entries: List[BeatmapPackEntryModel]
