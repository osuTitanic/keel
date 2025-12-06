
from pydantic import BaseModel
from datetime import datetime
from typing import List

from .user import UserModelCompact
from .beatmap import BeatmapModel

class ScoreModel(BaseModel):
    id: int
    user_id: int
    submitted_at: datetime
    mode: int
    status_pp: int
    status_score: int
    client_version: int
    client_version_string: str
    pp: float
    ppv1: float
    acc: float
    total_score: int
    max_combo: int
    mods: int
    perfect: bool
    passed: bool
    pinned: bool
    n300: int
    n100: int
    n50: int
    nMiss: int
    nGeki: int
    nKatu: int
    grade: str
    replay_views: int
    failtime: int | None
    beatmap: BeatmapModel
    user: UserModelCompact

class ScoreModelWithoutBeatmap(BaseModel):
    id: int
    user_id: int
    beatmap_id: int
    submitted_at: datetime
    mode: int
    status_pp: int
    status_score: int
    client_version: int
    client_version_string: str
    pp: float
    ppv1: float
    acc: float
    total_score: int
    max_combo: int
    mods: int
    perfect: bool
    passed: bool
    pinned: bool
    n300: int
    n100: int
    n50: int
    nMiss: int
    nGeki: int
    nKatu: int
    grade: str
    replay_views: int
    failtime: int | None
    user: UserModelCompact

class ScoreModelWithoutUser(BaseModel):
    id: int
    user_id: int
    submitted_at: datetime
    mode: int
    status_pp: int
    status_score: int
    client_version: int
    client_version_string: str
    pp: float
    ppv1: float
    acc: float
    total_score: int
    max_combo: int
    mods: int
    perfect: bool
    passed: bool
    pinned: bool
    n300: int
    n100: int
    n50: int
    nMiss: int
    nGeki: int
    nKatu: int
    grade: str
    replay_views: int
    failtime: int | None
    beatmap: BeatmapModel

class ScoreRecordsModel(BaseModel):
    osu: ScoreModel
    taiko: ScoreModel
    ctb: ScoreModel
    mania: ScoreModel

class ScoreCollectionResponse(BaseModel):
    total: int
    scores: List[ScoreModelWithoutUser]

class ScoreCollectionResponseWithoutBeatmap(BaseModel):
    total: int
    scores: List[ScoreModelWithoutBeatmap]

class ScorePinRequest(BaseModel):
    score_id: int
