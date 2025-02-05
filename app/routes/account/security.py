
from fastapi import HTTPException, APIRouter, Request

router = APIRouter()

@router.post("/security/email")
def change_email(request: Request):
    """Currently not implemented"""
    raise HTTPException(501, "Not implemented") # TODO

@router.post("/security/password")
def change_password(request: Request):
    """Currently not implemented"""
    raise HTTPException(501, "Not implemented") # TODO
