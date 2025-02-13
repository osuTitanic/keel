
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from typing import List

from app.models import PostModel, ErrorResponse
from app.common.database import topics, posts
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
        404: {"description": "Post not found", "model": ErrorResponse},
        301: {"description": "Redirect to the correct category"}
    }
)

@router.get("/{forum_id}/topics/{topic_id}/posts/{post_id}", response_model=PostModel)
def get_post(
    request: Request,
    forum_id: int,
    topic_id: int,
    post_id: int
) -> PostModel:
    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(404, "The requested post could not be found")

    if post.hidden:
        raise HTTPException(404, "The requested post could not be found")

    if post.topic_id != topic_id:
        return RedirectResponse(f"/forum/{post.forum_id}/topics/{post.topic_id}/posts/{post.id}")

    if post.forum_id != forum_id:
        return RedirectResponse(f"/forum/{post.forum_id}/topics/{post.topic_id}/posts/{post.id}")

    if post.deleted:
        post.content = '[ Deleted ]'

    return PostModel.model_validate(post, from_attributes=True)

@router.delete("/{forum_id}/topics/{topic_id}/posts/{post_id}", dependencies=[require_login])
@requires(["authenticated", "activated"])
def delete_post(
    request: Request,
    forum_id: int,
    topic_id: int,
    post_id: int
) -> dict:
    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(404, "The requested post could not be found")
    
    if post.hidden:
        raise HTTPException(404, "The requested post could not be found")
    
    if post.user_id != request.user.id and not request.user.is_moderator:
        raise HTTPException(403, "You do not have permission to delete this post")
    
    if post.edit_locked:
        raise HTTPException(403, "This post is locked and cannot be deleted")

    posts.update(
        post.id,
        {'deleted': True},
        session=request.state.db
    )

    return {}

@router.get("/{forum_id}/topics/{topic_id}/posts", response_model=List[PostModel])
def get_topic_posts(
    request: Request,
    forum_id: int,
    topic_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, le=50)
) -> List[PostModel]:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.forum_id != forum_id:
        return RedirectResponse(f"/forum/{topic.forum_id}/topics/{topic.id}/posts")

    topic_posts = posts.fetch_range_by_topic(
        topic.id,
        range=limit,
        offset=offset,
        session=request.state.db
    )

    for post in topic_posts:
        if post.hidden:
            topic_posts.remove(post)

        if post.deleted:
            post.content = '[ Deleted ]'

    return [
        PostModel.model_validate(post, from_attributes=True)
        for post in topic_posts
    ]
