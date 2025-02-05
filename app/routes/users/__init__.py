
from app.models import ErrorResponse
from fastapi import APIRouter

from . import achievements
from . import favourites
from . import playstyle
from . import activity
from . import beatmapsets
from . import friends
from . import profile
from . import history
from . import lookup
from . import pinned
from . import recent
from . import status
from . import first
from . import plays
from . import top

router = APIRouter(responses={404: {"model": ErrorResponse, "description": "Not found"}})
router.include_router(achievements.router)
router.include_router(beatmapsets.router)
router.include_router(favourites.router)
router.include_router(playstyle.router)
router.include_router(activity.router)
router.include_router(friends.router)
router.include_router(profile.router)
router.include_router(history.router)
router.include_router(lookup.router)
router.include_router(pinned.router)
router.include_router(recent.router)
router.include_router(status.router)
router.include_router(first.router)
router.include_router(plays.router)
router.include_router(top.router)
