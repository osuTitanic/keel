
from fastapi import APIRouter, Request
from app.models import ServerStatsModel

from . import beatmapsets
from . import multiplayer
from . import benchmarks
from . import resources
from . import rankings
from . import beatmaps
from . import account
from . import profile
from . import clients
from . import groups
from . import scores
from . import forum
from . import oauth
from . import chat

import app.session
import time

router = APIRouter()
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(forum.router, prefix="/forum", tags=["forum"])
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
router.include_router(groups.router, prefix="/groups", tags=["groups"])
router.include_router(scores.router, prefix="/scores", tags=["scores"])
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(clients.router, prefix="/clients", tags=["clients"])
router.include_router(account.router, prefix="/account", tags=["account"])
router.include_router(beatmaps.router, prefix="/beatmaps", tags=["beatmaps"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
router.include_router(resources.router, prefix="/resources", tags=["resources"])
router.include_router(benchmarks.router, prefix="/benchmarks", tags=["benchmarks"])
router.include_router(beatmapsets.router, prefix="/beatmapsets", tags=["beatmapsets"])
router.include_router(multiplayer.router, prefix="/multiplayer", tags=["multiplayer"])

@router.get('/stats', response_model=ServerStatsModel)
def server_stats(request: Request):
    return ServerStatsModel(
        uptime=round(time.time() - app.session.startup_time),
        total_scores=int(request.state.redis.get("bancho:totalscores") or 0),
        total_users=int(request.state.redis.get("bancho:totalusers") or 0),
        online_users=int(request.state.redis.get("bancho:users") or 0)
    )
