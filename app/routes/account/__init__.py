
from fastapi import APIRouter

from . import profile
from . import friends

router = APIRouter()
router.include_router(profile.router, tags=['profile'])
router.include_router(friends.router, tags=['friends'])
