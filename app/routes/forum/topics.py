
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from typing import List

from app.models import TopicModel, ErrorResponse
from app.common.database import forums, topics

router = APIRouter(
    responses={404: {"description": "The requested forum/topic was not found", "model": ErrorResponse}}
)

@router.get("/{forum_id}/topics", response_model=List[TopicModel])
def get_forum_topics(
    request: Request,
    forum_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, le=50)
) -> List[TopicModel]:
    if not (forum := forums.fetch_by_id(forum_id, request.state.db)):
        raise HTTPException(404, "The requested forum was not found")
    
    if forum.hidden:
        raise HTTPException(404, "The requested forum was not found")

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

@router.get("/{forum_id}/topics/{topic_id}", response_model=TopicModel)
def get_topic(
    request: Request,
    forum_id: int,
    topic_id: int
) -> TopicModel:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic was not found")

    if topic.forum_id != forum_id:
        return RedirectResponse(f"/forum/{topic.forum_id}/topics/{topic.id}")

    return TopicModel.model_validate(topic, from_attributes=True)
