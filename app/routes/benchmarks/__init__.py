
from fastapi import APIRouter

from . import leaderboard
from . import submit

router = APIRouter()
router.include_router(leaderboard.router)
router.include_router(submit.router)
