
from fastapi import APIRouter

from . import history
from . import submit
from . import search

router = APIRouter()
router.include_router(history.router)
router.include_router(submit.router)
router.include_router(search.router)
