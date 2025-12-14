
from app.models.beatmap import BeatmapsetModelWithoutBeatmaps
from app.models.user import UserModelCompact
from pydantic import BaseModel
from datetime import datetime

class NominationModelWithUser(BaseModel):
    set_id: int
    user_id: int
    time: datetime
    user: UserModelCompact

class NominationModelWithBeatmapset(BaseModel):
    set_id: int
    user_id: int
    time: datetime
    beatmapset: BeatmapsetModelWithoutBeatmaps
