from fastapi import APIRouter

from . import leaderboard
from . import submit
from . import submissions

router = APIRouter()

router.include_router(leaderboard.router)
router.include_router(submit.router)
router.include_router(submissions.router)
