
from fastapi import HTTPException, APIRouter, Request, Body
from typing import List

from app.models import BookmarkModel, BookmarkRequest, ErrorResponse
from app.common.constants import UserActivity
from app.common.database import users, topics
from app.common.helpers import activity
from app.security import require_login
from app.utils import requires

router = APIRouter(dependencies=[require_login])
responses = {404: {"description": "Bookmark/Topic not found", "model": ErrorResponse}}

@router.get("/bookmarks", response_model=List[BookmarkModel])
@requires("users.authenticated")
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

@router.get("/bookmarks/{topic_id}", response_model=BookmarkModel, responses=responses)
@requires("users.authenticated")
def get_bookmark(request: Request, topic_id: int):
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    bookmark = topics.fetch_bookmark(
        topic_id,
        request.user.id,
        request.state.db
    )

    if not bookmark:
        raise HTTPException(404, "The requested bookmark could not be found")

    return BookmarkModel.model_validate(bookmark, from_attributes=True)

@router.post("/bookmarks", response_model=BookmarkModel, responses=responses)
@requires("forum.bookmarks.create")
def create_bookmark(request: Request, data: BookmarkRequest = Body(...)):
    if not (topic := topics.fetch_one(data.topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    bookmark = topics.add_bookmark(
        topic.id,
        request.user.id,
        request.state.db
    )

    activity.submit(
        request.user.id, None,
        UserActivity.ForumBookmarked,
        {
            'username': request.user.name,
            'topic_name': topic.title,
            'topic_id': topic.id
        },
        is_hidden=True,
        session=request.state.db
    )

    return BookmarkModel.model_validate(bookmark, from_attributes=True)

@router.delete("/bookmarks/{topic_id}", responses=responses)
@requires("forum.bookmarks.delete")
def delete_bookmark(request: Request, topic_id: int) -> dict:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    rows = topics.delete_bookmark(
        topic.id,
        request.user.id,
        request.state.db
    )

    if not rows:
        raise HTTPException(404, "The requested bookmark could not be found")

    activity.submit(
        request.user.id, None,
        UserActivity.ForumUnbookmarked,
        {
            'username': request.user.name,
            'topic_name': topic.title,
            'topic_id': topic.id
        },
        is_hidden=True,
        session=request.state.db
    )

    return {}
