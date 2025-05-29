
from fastapi import APIRouter
from . import infringements

router = APIRouter()
router.include_router(infringements.router)
