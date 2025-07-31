
from app.common.constants import ClientStatus, GameMode, Mods
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict

from .groups import GroupEntryModel

class RelationshipModel(BaseModel):
    user_id: int
    target_id: int
    status: int

class RelationshipResponse(BaseModel):
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
    reserved: bool

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
    banner: str | None
    website: str | None
    discord: str | None
    twitter: str | None
    location: str | None
    interests: str | None

class UserModel(UserModelCompact):
    relationships: List[RelationshipModel]
    achievements: List[AchievementModel]
    names: List[NameHistoryModel]
    badges: List[BadgeModel]
    stats: List[StatsModel]
    groups: List[GroupEntryModel]
    rankings: Dict[int, dict | None]

class UserModelWithStats(UserModelCompact):
    stats: List[StatsModel] | None = None

class ProfileUpdateModel(BaseModel):
    interests: str | None = None
    location: str | None = None
    website: str | None = None
    discord: str | None = None
    twitter: str | None = None

class StatusStatsModel(BaseModel):
    rscore: int
    tscore: int
    accuracy: float
    playcount: int
    rank: int
    pp: float

class RankingModel(BaseModel):
    global_rank: int
    ppv1_rank: int
    score_rank: int
    total_score_rank: int

class StatusModel(BaseModel):
    action: ClientStatus
    version: int | None
    mode: GameMode
    mods: Mods
    beatmap_id: int
    beatmap_checksum: str
    beatmap_text: str
    rankings: RankingModel
    stats: StatusStatsModel
