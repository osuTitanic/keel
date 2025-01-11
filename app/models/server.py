
from __future__ import annotations
from pydantic import BaseModel

class ServerStatsModel(BaseModel):
    uptime: int
    total_scores: int
    total_users: int
    online_users: int
