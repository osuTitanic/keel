
from fastapi import APIRouter

from . import channels
from . import search
from . import dms

router = APIRouter()
router.include_router(channels.router)
router.include_router(search.router)
router.include_router(dms.router)
