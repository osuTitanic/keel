
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from typing import List

from .groups import GroupEntryModel

class RelationshipModel(BaseModel):
    user_id: int
    target_id: int
    status: int

class RelationshipResponseModel(BaseModel):
    status: str

class AchievementModel(BaseModel):
    user_id: int
    name: str
    category: str
    filename: str
    unlocked_at: datetime

class FavouritesModel(BaseModel):
    user_id: int
    set_id: int
    created_at: datetime

class BadgeModel(BaseModel):
    id: int
    user_id: int
    created: datetime
    badge_icon: str
    badge_url: str | None
    badge_description: str | None

class NameHistoryModel(BaseModel):
    id: int
    user_id: int
    changed_at: datetime
    name: str

class StatsModel(BaseModel):
    mode: int
    rank: int
    tscore: int
    rscore: int
    pp: float
    ppv1: float
    playcount: int
    playtime: int
    acc: float
    max_combo: int
    total_hits: int
    replay_views: int
    xh_count: int
    x_count: int
    sh_count: int
    s_count: int
    a_count: int
    b_count: int
    c_count: int
    d_count: int

class UserModel(BaseModel):
    id: int
    name: str
    country: str
    created_at: datetime
    latest_activity: datetime
    silence_end: datetime | None
    restricted: bool
    activated: bool
    preferred_mode: int
    playstyle: int
    userpage: str | None
    signature: str | None
    banner: str | None
    website: str | None
    discord: str | None
    twitter: str | None
    location: str | None
    interests: str | None

    relationships: List[RelationshipModel]
    achievements: List[AchievementModel]
    names: List[NameHistoryModel]
    badges: List[BadgeModel]
    stats: List[StatsModel]
    groups: List[GroupEntryModel]

class UserModelCompact(BaseModel):
    id: int
    name: str
    country: str
    created_at: datetime
    latest_activity: datetime
    restricted: bool
    activated: bool
    preferred_mode: int
    playstyle: int
    userpage: str | None
    signature: str | None
    banner: str | None
    website: str | None
    discord: str | None
    twitter: str | None
    location: str | None
    interests: str | None

class ProfileUpdateModel(BaseModel):
    interests: str | None = None
    location: str | None = None
    website: str | None = None
    discord: str | None = None
    twitter: str | None = None
