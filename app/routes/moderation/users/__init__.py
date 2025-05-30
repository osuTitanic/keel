
from app.security import require_login
from fastapi import APIRouter

from . import infringements
from . import reports

router = APIRouter(dependencies=[require_login])
router.include_router(infringements.router)
router.include_router(reports.router)
