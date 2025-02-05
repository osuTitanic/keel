
from fastapi import APIRouter

from . import notifications
from . import security
from . import register
from . import profile
from . import friends
from . import reset
from . import login

router = APIRouter()
router.include_router(notifications.router)
router.include_router(security.router)
router.include_router(register.router)
router.include_router(profile.router)
router.include_router(friends.router)
router.include_router(reset.router)
router.include_router(login.router)
