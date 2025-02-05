
from app.models import ErrorResponse
from fastapi import APIRouter

from . import osz2
from . import osz
from . import osu
from . import mp3
from . import mt

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"}
    }
)

router.include_router(osz2.router)
router.include_router(osz.router)
router.include_router(osu.router)
router.include_router(mp3.router)
router.include_router(mt.router)
