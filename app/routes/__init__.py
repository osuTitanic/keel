
from fastapi import APIRouter
from . import beatmapsets
from . import multiplayer
from . import moderation
from . import benchmarks
from . import resources
from . import rankings
from . import beatmaps
from . import support
from . import account
from . import releases
from . import groups
from . import scores
from . import events
from . import forum
from . import stats
from . import users
from . import oauth
from . import media
from . import chat

router = APIRouter(responses={500: {"description": "Internal Server Error"}})
router.include_router(stats.router)
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(media.router, prefix="/media", tags=["media"])
router.include_router(forum.router, prefix="/forum", tags=["forum"])
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(groups.router, prefix="/groups", tags=["groups"])
router.include_router(scores.router, prefix="/scores", tags=["scores"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(account.router, prefix="/account", tags=["account"])
router.include_router(support.router, prefix="/support", tags=["support"])
router.include_router(beatmaps.router, prefix="/beatmaps", tags=["beatmaps"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
router.include_router(releases.router, prefix="/releases", tags=["releases"])
router.include_router(benchmarks.router, prefix="/benchmarks", tags=["benchmarks"])
router.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
router.include_router(beatmapsets.router, prefix="/beatmapsets", tags=["beatmapsets"])
router.include_router(multiplayer.router, prefix="/multiplayer", tags=["multiplayer"])
router.include_router(resources.router, prefix="/resources", tags=["internal resources"])
