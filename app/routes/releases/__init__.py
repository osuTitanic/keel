
from fastapi import APIRouter

from . import official
from . import titanic
from . import modded

router = APIRouter()
router.include_router(official.router)
router.include_router(titanic.router)
router.include_router(modded.router)
