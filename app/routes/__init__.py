
from fastapi import APIRouter
from app.models import ServerStats
from . import oauth

import app.session
import time

router = APIRouter()
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])

@router.get('/', response_model=ServerStats)
def server_stats():
    return ServerStats(
        uptime=round(time.time() - app.session.startup_time),
        total_scores=int(app.session.redis.get("bancho:totalscores") or 0),
        total_users=int(app.session.redis.get("bancho:totalusers") or 0),
        online_users=int(app.session.redis.get("bancho:users") or 0)
    )

# /stats was used in the old api, so we'll keep it for compatibility
router.get("/stats", response_model=ServerStats)(server_stats)
