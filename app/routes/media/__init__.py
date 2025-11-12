
from fastapi import APIRouter
from . import bitview

router = APIRouter(include_in_schema=False)
router.include_router(bitview.router)
