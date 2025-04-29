
from pydantic import BaseModel
from typing import List, Dict

class BeatmapModeStatsModel(BaseModel):
    mode: int
    count_graveyard: int
    count_wip: int
    count_pending: int
    count_ranked: int
    count_approved: int
    count_qualified: int
    count_loved: int

class ServerStatsModel(BaseModel):
    uptime: int
    online_users: int
    total_users: int
    total_scores: int
    total_beatmaps: int
    total_beatmapsets: int
    beatmap_modes: Dict[int, BeatmapModeStatsModel]
