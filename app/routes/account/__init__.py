
from fastapi import APIRouter

from . import register
from . import profile
from . import friends
from . import reset

router = APIRouter()
router.include_router(register.router)
router.include_router(profile.router)
router.include_router(friends.router)
router.include_router(reset.router)
