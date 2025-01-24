
from fastapi import APIRouter

from . import channels
from . import submit
from . import search

router = APIRouter()
router.include_router(channels.router)
router.include_router(submit.router)
router.include_router(search.router)
