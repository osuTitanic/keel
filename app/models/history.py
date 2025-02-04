
from pydantic import BaseModel
from datetime import datetime

class RankHistoryModel(BaseModel):
    time: datetime
    mode: int
    rscore: int
    pp: int | float
    ppv1: int | float
    pp_vn: int | float
    pp_rx: int | float
    pp_ap: int | float
    global_rank: int
    country_rank: int
    score_rank: int
    ppv1_rank: int
    pp_vn_rank: int
    pp_rx_rank: int
    pp_ap_rank: int

class PlaysHistoryModel(BaseModel):
    mode: int
    year: int
    month: int
    plays: int

class ReplayHistoryModel(BaseModel):
    mode: int
    year: int
    month: int
    replay_views: int
