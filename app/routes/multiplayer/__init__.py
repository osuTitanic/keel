from fastapi import APIRouter

from . import events, management, match

router = APIRouter()
router.include_router(management.router, prefix="/matches")
router.include_router(events.router, prefix="/matches")
router.include_router(match.router, prefix="/matches")
