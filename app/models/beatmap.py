
from pydantic import BaseModel, computed_field
from datetime import datetime

class BeatmapsetModelWithoutBeatmaps(BaseModel):
    id: int
    title: str | None
    artist: str | None
    creator: str | None
    source: str | None
    tags: str | None
    creator_id: int | None
    topic_id: int | None
    status: int
    has_video: bool
    has_storyboard: bool
    offset: int
    server: int
    download_server: int
    available: bool
    enhanced: bool
    language_id: int
    genre_id: int
    display_title: str
    created_at: datetime
    last_update: datetime
    approved_at: datetime | None
    approved_by: int | None
    rating_average: float
    rating_count: int
    total_playcount: int
    max_diff: float
    osz_filesize: int
    osz_filesize_novideo: int

    @computed_field
    @property
    def ratings(self) -> float:
        # Deprecated: replaced by "rating_average"
        return self.rating_average

class BeatmapModel(BaseModel):
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
    drain_length: int
    max_combo: int
    bpm: float
    cs: float
    ar: float
    od: float
    hp: float
    diff: float
    count_normal: int
    count_slider: int
    count_spinner: int
    slider_multiplier: float
    beatmapset: BeatmapsetModelWithoutBeatmaps

class BeatmapPlaysModel(BaseModel):
    beatmap: BeatmapModel
    count: int
