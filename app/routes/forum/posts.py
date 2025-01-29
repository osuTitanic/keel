
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from typing import List

from app.common.database import topics, posts
from app.models import PostModel

router = APIRouter()

@router.get("/{forum_id}/topics/{topic_id}/posts", response_model=List[PostModel])
def get_topic_posts(
    request: Request,
    forum_id: int,
    topic_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, le=50)
) -> List[PostModel]:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "Topic not found")

    if topic.forum_id != forum_id:
        return RedirectResponse(f"/forum/{topic.forum_id}/topics/{topic.id}/posts")

    topic_posts = posts.fetch_range_by_topic(
        topic.id,
        range=limit,
        offset=offset,
        session=request.state.db
    )

    for post in topic_posts:
        if not post.hidden:
            continue

        post.content = '[ Deleted ]'

    return [
        PostModel.model_validate(post, from_attributes=True)
        for post in topic_posts
    ]
