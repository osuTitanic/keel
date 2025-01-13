
from fastapi import HTTPException, APIRouter, Request

router = APIRouter()

@router.get("/notifications")
def get_notifications(request: Request):
    raise HTTPException(501, "Not implemented") # TODO

@router.delete("/notifications")
def delete_notifications(request: Request):
    raise HTTPException(501, "Not implemented") # TODO
