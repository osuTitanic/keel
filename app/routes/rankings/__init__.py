
from fastapi import APIRouter

from . import country
from . import regular
from . import kudosu

router = APIRouter()
router.include_router(country.router)
router.include_router(regular.router)
router.include_router(kudosu.router)
