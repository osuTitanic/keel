
from fastapi import APIRouter

from . import register
from . import profile
from . import friends

router = APIRouter()
router.include_router(register.router, tags=['register'])
router.include_router(profile.router, tags=['profile'])
router.include_router(friends.router, tags=['friends'])
