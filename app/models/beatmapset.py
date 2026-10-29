
from app.common.constants import BeatmapLanguage, BeatmapGenre
from app.models.beatmap import BeatmapModelCompact
from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime
from typing import List

class BeatmapsetModelCompact(BaseModel):
    id: int
    title: str | None
    title_unicode: str | None
    artist: str | None
    artist_unicode: str | None
    creator: str | None
    source: str | None
    source_unicode: str | None
    tags: str | None
    creator_id: int | None
    topic_id: int | None
    post_id: int | None
    status: int
    has_video: bool
    has_storyboard: bool
    offset: int
    server: int
    download_server: int
    available: bool
    enhanced: bool
    explicit: bool
    language_id: int
    genre_id: int
    display_title: str
    created_at: datetime
    last_update: datetime
    approved_at: datetime | None
    approved_by: int | None
    rating_average: float
    rating_count: int
    favourite_count: int
    total_playcount: int
    max_diff: float
    osz_filesize: int
    osz_filesize_novideo: int

    @computed_field
    @property
    def ratings(self) -> float:
        # Deprecated: replaced by "rating_average"
        return self.rating_average

    @computed_field
    @property
    def favourites(self) -> float:
        # Deprecated: replaced by "favourite_count"
        return self.favourite_count

class BeatmapsetModel(BeatmapsetModelCompact):
    beatmaps: List[BeatmapModelCompact]

class BeatmapUpdateRequest(BaseModel):
    id: int
    md5: str | None
    version: str | None
    filename: str | None

class BeatmapsetUpdateRequest(BaseModel):
    title: str | None
    title_unicode: str | None
    artist: str | None
    artist_unicode: str | None
    source: str | None
    source_unicode: str | None
    offset: int = 0
    tags: str = ""
    language: BeatmapLanguage = BeatmapLanguage.Unspecified
    genre: BeatmapGenre = BeatmapGenre.Unspecified
    download_server: int | None = None
    display_title: str | None = None
    enhanced: bool = False
    explicit: bool = False
    available: bool = True
    beatmap_updates: List[BeatmapUpdateRequest] = Field(default_factory=list)

class BeatmapsetDescriptionUpdate(BaseModel):
    bbcode: str

class BeatmapsetOwnerUpdate(BaseModel):
    user_id: int

class BeatmapsetLinkRequest(BaseModel):
    topic_id: int
