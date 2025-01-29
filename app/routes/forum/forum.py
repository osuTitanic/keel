
from fastapi import HTTPException, APIRouter, Request
from app.common.database import forums
from app.models import ForumModel

router = APIRouter()

@router.get("/")
def get_main_forums(request: Request):
    return [
        ForumModel.model_validate(forum, from_attributes=True)
        for forum in forums.fetch_main_forums(request.state.db)
    ]

@router.get("/{forum_id}")
def get_forum(request: Request, forum_id: int):
    if not (forum := forums.fetch_by_id(forum_id, request.state.db)):
        raise HTTPException(404, "Forum not found")
    
    if forum.hidden:
        raise HTTPException(404, "Forum not found")

    return ForumModel.model_validate(forum, from_attributes=True)
