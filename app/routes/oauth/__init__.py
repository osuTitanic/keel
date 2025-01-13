
from fastapi import APIRouter
from . import token

router = APIRouter()
router.include_router(token.router)
