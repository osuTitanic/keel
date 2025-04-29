
from pydantic import BaseModel

class ServerStatsModel(BaseModel):
    uptime: int
    online_users: int
    total_users: int
    total_scores: int
    total_beatmaps: int
    total_beatmapsets: int
