
from fastapi import HTTPException, APIRouter, Request
from app.utils import requires

router = APIRouter()

@router.post("/")
@requires("tmg")
def upload_client(request: Request):
    """Currently not implemented"""
    raise HTTPException(501, "Not implemented")
