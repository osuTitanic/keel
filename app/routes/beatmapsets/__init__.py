
from fastapi import APIRouter

from . import beatmapset
from . import nomination
from . import resources
from . import kudosu
from . import search
from . import status
from . import packs
from . import nuke

router = APIRouter()
router.include_router(kudosu.router, tags=["kudosu"])
router.include_router(beatmapset.router)
router.include_router(nomination.router)
router.include_router(resources.router)
router.include_router(search.router)
router.include_router(status.router)
router.include_router(packs.router)
router.include_router(nuke.router)
