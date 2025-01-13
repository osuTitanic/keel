
from fastapi import APIRouter

from . import events
from . import match

router = APIRouter()
router.include_router(events.router)
router.include_router(match.router)
