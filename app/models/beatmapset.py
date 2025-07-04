
from app.common.constants import BeatmapLanguage, BeatmapGenre
from app.common.database import DBRating, DBFavourite
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List

class BeatmapModelWithoutSet(BaseModel):
    id: int
    set_id: int
    mode: int
    md5: str
    status: int
    version: str
    filename: str
    created_at: datetime
    last_update: datetime
    playcount: int
    passcount: int
    total_length: int
    max_combo: int
    bpm: float
    cs: float
    ar: float
    od: float
    hp: float
    diff: float

class BeatmapsetModel(BaseModel):
    id: int
    title: str | None
    artist: str | None
    creator: str | None
    source: str | None
    tags: str | None
    creator_id: int | None
    status: int
    has_video: bool
    has_storyboard: bool
    server: int
    available: bool
    enhanced: bool
    created_at: datetime
    approved_at: datetime | None
    last_update: datetime
    osz_filesize: int
    osz_filesize_novideo: int
    display_title: str
    language_id: int
    genre_id: int
    ratings: list
    favourites: list
    beatmaps: List[BeatmapModelWithoutSet]

    @field_validator('ratings')
    def avg_rating(cls, ratings: List[DBRating]) -> float:
        if not ratings:
            return 0.0

        ratings = [r.rating for r in ratings]
        return sum(ratings) / len(ratings)

    @field_validator('favourites')
    def sum_favourites(cls, favourites: List[DBFavourite]) -> int:
        return len(favourites)

class BeatmapUpdateRequest(BaseModel):
    offset: int = 0
    tags: str = ""
    language: BeatmapLanguage = BeatmapLanguage.Unspecified
    genre: BeatmapGenre = BeatmapGenre.Unspecified
    download_server: int | None = None
    display_title: str | None = None
    enhanced: bool = False
