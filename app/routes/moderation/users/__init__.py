
from app.security import require_login
from fastapi import APIRouter

from . import infringements
from . import reports
from . import profile
from . import badges
from . import logins
from . import names

router = APIRouter(dependencies=[require_login])
router.include_router(infringements.router)
router.include_router(reports.router)
router.include_router(profile.router)
router.include_router(badges.router)
router.include_router(logins.router)
router.include_router(names.router)
