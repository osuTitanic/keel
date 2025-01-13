
from fastapi import APIRouter

from . import regular
from . import country

router = APIRouter()
router.include_router(regular.router)
router.include_router(country.router)
