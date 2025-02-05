
from fastapi import HTTPException, APIRouter, Request

router = APIRouter()

@router.post("/search")
def search_chat_messages(request: Request):
    """Currently not implemented"""
    raise HTTPException(501, "Not implemented")
