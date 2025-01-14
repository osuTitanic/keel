
from fastapi import APIRouter

from . import resources
from . import beatmap
from . import scores

router = APIRouter()
router.include_router(resources.router)
router.include_router(beatmap.router)
router.include_router(scores.router)