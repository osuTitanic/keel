
from fastapi import HTTPException, APIRouter, Request

router = APIRouter()

@router.post("/security/email")
def change_email(request: Request):
    raise HTTPException(501, "Not implemented") # TODO

@router.post("/security/password")
def change_password(request: Request):
    raise HTTPException(501, "Not implemented") # TODO
