
from fastapi import HTTPException, APIRouter, Request

router = APIRouter()

@router.get("/search")
def search_forum(request: Request):
    """Currently not implemented"""
    raise HTTPException(501, "Not implemented")
