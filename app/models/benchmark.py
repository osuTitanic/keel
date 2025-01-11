
from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime

from .user import UserModel

class BenchmarkModel(BaseModel):
    id: int
    smoothness: float
    framerate: int
    score: int
    grade: str
    created_at: datetime
    client: str
    hardware: dict | None
    user: UserModel
