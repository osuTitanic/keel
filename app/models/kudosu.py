
from pydantic import BaseModel
from datetime import datetime

from .beatmapset import BeatmapsetModel
from .user import UserModelCompact
from .forums import PostModel

class KudosuModel(BaseModel):
    id: int
    target: UserModelCompact
    sender: UserModelCompact
    beatmapset: BeatmapsetModel
    post: PostModel
    amount: int
    time: datetime

class KudosuWithoutSetModel(BaseModel):
    id: int
    target: UserModelCompact
    sender: UserModelCompact
    post: PostModel
    amount: int
    time: datetime
