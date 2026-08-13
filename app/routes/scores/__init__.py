
from fastapi import APIRouter

from . import records
from . import replays
from . import scores

router = APIRouter()
router.include_router(records.router)
router.include_router(replays.router)
router.include_router(scores.router)
