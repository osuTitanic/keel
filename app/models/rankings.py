
from app.common.constants import GameMode
from functools import cached_property
from pydantic import BaseModel
from enum import Enum

from .user import UserModel

class ModeAlias(str, Enum):
    Osu = 'osu'
    Taiko = 'taiko'
    CatchTheBeat = 'fruits'
    OsuMania = 'mania'

    @cached_property
    def integer(self) -> int:
        return GameMode.from_alias(self).value

class OrderType(str, Enum):
    Performance = 'performance'
    RankedScore = 'rscore'
    TotalScore = 'tscore'
    Country = 'country'
    PPv1 = 'ppv1'

class RankingStatsModel(BaseModel):
    global_rank: int
    country_rank: int
    score_rank: int
    score_rank_country: int
    total_score_rank: int
    total_score_rank_country: int
    ppv1_rank: int
    ppv1_rank_country: int

class CountryStatsModel(BaseModel):
    average_performance: float
    total_performance: float
    total_rscore: int
    total_tscore: int
    total_users: int

class RankingEntryModel(BaseModel):
    index: int
    score: float
    user: UserModel
    stats: RankingStatsModel

class CountryEntryModel(BaseModel):
    index: int
    country_name: str
    country_acronym: str
    stats: CountryStatsModel
