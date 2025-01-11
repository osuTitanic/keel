
from fastapi import APIRouter
from . import oauth

router = APIRouter()
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
