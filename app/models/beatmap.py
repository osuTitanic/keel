
from pydantic import BaseModel, computed_field
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.beatmapset import BeatmapsetModelCompact

class BeatmapModelCompact(BaseModel):
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

class BeatmapModel(BeatmapModelCompact):
    beatmapset: "BeatmapsetModelCompact"

class BeatmapPlaysModel(BaseModel):
    beatmap: BeatmapModel
    count: int
