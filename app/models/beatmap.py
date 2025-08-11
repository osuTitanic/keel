
from pydantic import BaseModel
from datetime import datetime

class BeatmapsetModelWithoutBeatmaps(BaseModel):
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
    beatmapset: BeatmapsetModelWithoutBeatmaps

class BeatmapPlaysModel(BaseModel):
    beatmap: BeatmapModel
    count: int
