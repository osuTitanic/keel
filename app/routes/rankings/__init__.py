
from fastapi import APIRouter

from . import country
from . import regular

router = APIRouter()
router.include_router(country.router)
router.include_router(regular.router)
