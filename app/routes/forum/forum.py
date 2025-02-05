
from fastapi import HTTPException, APIRouter, Request
from app.models import ForumModel, ErrorResponse
from app.common.database import forums

router = APIRouter(
    responses={404: {"description": "The requested forum was not found", "model": ErrorResponse}}
)

@router.get("/", response_model=list[ForumModel])
def get_main_forums(request: Request):
    return [
        ForumModel.model_validate(forum, from_attributes=True)
        for forum in forums.fetch_main_forums(request.state.db)
    ]

@router.get("/{forum_id}", response_model=ForumModel)
def get_forum(request: Request, forum_id: int):
    if not (forum := forums.fetch_by_id(forum_id, request.state.db)):
        raise HTTPException(404, "The requested forum was not found")
    
    if forum.hidden:
        raise HTTPException(404, "The requested forum was not found")

    return ForumModel.model_validate(forum, from_attributes=True)
