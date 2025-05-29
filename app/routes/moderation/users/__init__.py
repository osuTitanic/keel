
from app.security import require_login
from fastapi import APIRouter
from . import infringements

router = APIRouter(dependencies=[require_login])
router.include_router(infringements.router)
