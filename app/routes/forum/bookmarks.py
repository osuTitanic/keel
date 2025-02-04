
from fastapi import HTTPException, APIRouter, Request, Body
from typing import List

from app.models import BookmarkModel, BookmarkRequest
from app.common.database import users, topics
from app.security import require_login
from app.utils import requires

router = APIRouter(dependencies=[require_login])

@router.get("/bookmarks", response_model=List[BookmarkModel])
@requires("authenticated")
def get_bookmarks(request: Request):
    bookmarks = users.fetch_bookmarks(
        request.user.id,
        request.state.db
    )

    bookmarks = [
        bookmark
        for bookmark in bookmarks
        if not bookmark.topic.hidden
    ]

    return [
        BookmarkModel.model_validate(bookmark, from_attributes=True)
        for bookmark in bookmarks
    ]

@router.get("/bookmarks/{topic_id}")
@requires("authenticated")
def get_bookmark(request: Request, topic_id: int):
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic was not found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic was not found")

    bookmark = topics.fetch_bookmark(
        topic_id,
        request.user.id,
        request.state.db
    )

    if not bookmark:
        raise HTTPException(404, "The requested bookmark was not found")

    return BookmarkModel.model_validate(bookmark, from_attributes=True)

@router.post("/bookmarks", response_model=BookmarkModel)
@requires("authenticated")
def create_bookmark(request: Request, data: BookmarkRequest = Body(...)):
    if not (topic := topics.fetch_one(data.topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic was not found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic was not found")

    bookmark = topics.add_bookmark(
        topic.id,
        request.user.id,
        request.state.db
    )

    return BookmarkModel.model_validate(bookmark, from_attributes=True)

@router.delete("/bookmarks/{topic_id}")
@requires("authenticated")
def delete_bookmark(request: Request, topic_id: int) -> dict:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic was not found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic was not found")

    rows = topics.delete_bookmark(
        topic.id,
        request.user.id,
        request.state.db
    )

    if not rows:
        raise HTTPException(404, "The requested bookmark was not found")
    
    return {}
