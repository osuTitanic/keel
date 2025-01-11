
from __future__ import annotations
from pydantic import BaseModel
from app.common.constants import (
    BeatmapCategory,
    BeatmapLanguage,
    BeatmapSortBy,
    BeatmapGenre,
    BeatmapOrder,
    GameMode
)

class SearchRequest(BaseModel):
    language: BeatmapLanguage | None = None
    genre: BeatmapGenre | None = None
    mode: GameMode | None = None
    uncleared: bool | None = None
    unplayed: bool | None = None
    cleared: bool | None = None
    played: bool | None = None
    query: str | None = None
    category: BeatmapCategory = BeatmapCategory.Leaderboard
    order: BeatmapOrder = BeatmapOrder.Descending
    sort: BeatmapSortBy = BeatmapSortBy.Ranked
    storyboard: bool = False
    video: bool = False
    titanic: bool = False
    page: int = 0
