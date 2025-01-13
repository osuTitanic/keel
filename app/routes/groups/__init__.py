
from fastapi import APIRouter

from . import management
from . import group

router = APIRouter()
router.include_router(management.router)
router.include_router(group.router)
