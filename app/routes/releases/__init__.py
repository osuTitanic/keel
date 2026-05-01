
from fastapi import APIRouter

from . import changelog
from . import releases
from . import upload
from . import update

router = APIRouter()
router.include_router(changelog.router)
router.include_router(releases.router)
router.include_router(upload.router)
router.include_router(update.router)
