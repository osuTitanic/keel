
from fastapi import APIRouter
from . import friends

router = APIRouter()
router.include_router(friends.router, tags=['friends'])
