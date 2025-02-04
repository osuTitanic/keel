
from pydantic import BaseModel
from datetime import datetime
from typing import List

from .beatmap import BeatmapModel
from .user import UserModel

class ScoreModel(BaseModel):
    id: int
    user_id: int
    submitted_at: datetime
    mode: int
    status_pp: int
    status_score: int
    client_version: int
    pp: float
    acc: float
    total_score: int
    max_combo: int
    mods: int
    perfect: bool
    n300: int
    n100: int
    n50: int
    nMiss: int
    nGeki: int
    nKatu: int
    grade: str
    pinned: bool
    beatmap: BeatmapModel
    user: UserModel

class ScoreModelWithoutBeatmap(BaseModel):
    id: int
    user_id: int
    submitted_at: datetime
    mode: int
    status_pp: int
    status_score: int
    client_version: int
    pp: float
    acc: float
    total_score: int
    max_combo: int
    mods: int
    perfect: bool
    n300: int
    n100: int
    n50: int
    nMiss: int
    nGeki: int
    nKatu: int
    grade: str
    pinned: bool
    user: UserModel

class ScoreModelWithoutUser(BaseModel):
    id: int
    user_id: int
    submitted_at: datetime
    mode: int
    status_pp: int
    status_score: int
    client_version: int
    pp: float
    acc: float
    total_score: int
    max_combo: int
    mods: int
    perfect: bool
    n300: int
    n100: int
    n50: int
    nMiss: int
    nGeki: int
    nKatu: int
    grade: str
    pinned: bool
    beatmap: BeatmapModel

class ScoreRecordsModel(BaseModel):
    osu_vanilla: ScoreModel
    osu_relax: ScoreModel
    osu_autopilot: ScoreModel
    taiko_vanilla: ScoreModel
    taiko_relax: ScoreModel
    ctb_vanilla: ScoreModel
    ctb_relax: ScoreModel
    mania: ScoreModel

class ScoreCollectionResponse(BaseModel):
    total: int
    scores: List[ScoreModelWithoutUser]

class ScorePinRequest(BaseModel):
    score_id: int
