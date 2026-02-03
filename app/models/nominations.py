
from app.models.beatmapset import BeatmapsetModelCompact
from app.models.user import UserModelCompact
from pydantic import BaseModel
from datetime import datetime

class NominationModelCompact(BaseModel):
    set_id: int
    user_id: int
    time: datetime

class NominationModel(NominationModelCompact):
    user: UserModelCompact
    beatmapset: BeatmapsetModelCompact

class NominationModelWithUser(NominationModelCompact):
    user: UserModelCompact

class NominationModelWithBeatmapset(NominationModelCompact):
    beatmapset: BeatmapsetModelCompact
