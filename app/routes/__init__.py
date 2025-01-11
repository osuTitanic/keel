
from fastapi import APIRouter
from app.models import ServerStatsModel

from . import account
from . import oauth

import app.session
import time

router = APIRouter()
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
router.include_router(account.router, prefix="/account", tags=["account"])

@router.get('/stats', response_model=ServerStatsModel)
def server_stats():
    return ServerStatsModel(
        uptime=round(time.time() - app.session.startup_time),
        total_scores=int(app.session.redis.get("bancho:totalscores") or 0),
        total_users=int(app.session.redis.get("bancho:totalusers") or 0),
        online_users=int(app.session.redis.get("bancho:users") or 0)
    )
