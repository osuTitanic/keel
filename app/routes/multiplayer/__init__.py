from fastapi import APIRouter

from . import events, management, match

router = APIRouter(prefix="/matches")
router.include_router(management.router)
router.include_router(events.router)
router.include_router(match.router)
