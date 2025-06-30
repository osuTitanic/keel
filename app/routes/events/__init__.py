
from fastapi import APIRouter

from . import ws

router = APIRouter()
router.include_router(ws.router, prefix="/ws")
