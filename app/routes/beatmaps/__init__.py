
from fastapi import APIRouter

from . import collaboration
from . import resources
from . import beatmap
from . import scores
from . import lookup

router = APIRouter()
router.include_router(collaboration.router)
router.include_router(resources.router)
router.include_router(beatmap.router)
router.include_router(scores.router)
router.include_router(lookup.router)
