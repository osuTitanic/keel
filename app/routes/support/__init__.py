
from fastapi import APIRouter
from . import kofi

router = APIRouter(include_in_schema=False)
router.include_router(kofi.router, prefix="/kofi")
