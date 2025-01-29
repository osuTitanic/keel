
from fastapi import HTTPException, APIRouter, Request, Query
from typing import List

from app.common.database import forums, topics
from app.models import TopicModel

router = APIRouter()

@router.get("/{forum_id}/topics")
def get_forum_topics(
    request: Request,
    forum_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, le=50)
) -> List[TopicModel]:
    if not (forum := forums.fetch_by_id(forum_id, request.state.db)):
        raise HTTPException(404, "Forum not found")
    
    if forum.hidden:
        raise HTTPException(404, "Forum not found")

    forum_topics = topics.fetch_recent_many(
        forum.id,
        limit=limit,
        offset=offset,
        session=request.state.db
    )

    return [
        TopicModel.model_validate(topic, from_attributes=True)
        for topic in forum_topics
    ]
