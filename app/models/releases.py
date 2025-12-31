
from pydantic import BaseModel
from datetime import datetime
from typing import List

class TitanicReleaseModel(BaseModel):
    name: str
    description: str
    category: str
    known_bugs: str | None
    supported: bool
    preview: bool
    downloads: List[str]
    screenshots: List[str]
    created_at: datetime

class ModdedReleaseModel(BaseModel):
    name: str
    description: str
    creator_id: int | None
    topic_id: int | None
    client_version: int
    client_extension: str
    created_at: datetime

class OsuChangelogModel(BaseModel):
    id: int
    text: str
    type: str
    branch: str
    author: str
    area: str | None
    created_at: datetime
