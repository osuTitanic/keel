
from fastapi import HTTPException, APIRouter, Request, Query, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List

from app.common.database.objects import DBForumTopic, DBUser, DBForumPost
from app.models import TopicModel, ErrorResponse, TopicCreateRequest
from app.common.database import forums, topics, posts
from app.common.constants import UserActivity
from app.common.helpers import activity
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={404: {"description": "Forum/Topic not found", "model": ErrorResponse}}
)

@router.get("/{forum_id}/topics", response_model=List[TopicModel])
def get_forum_topics(
    request: Request,
    forum_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, le=50)
) -> List[TopicModel]:
    if not (forum := forums.fetch_by_id(forum_id, request.state.db)):
        raise HTTPException(404, "The requested forum could not be found")
    
    if forum.hidden:
        raise HTTPException(404, "The requested forum could not be found")

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
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    if topic.forum_id != forum_id:
        return RedirectResponse(f"/forum/{topic.forum_id}/topics/{topic.id}")

    return TopicModel.model_validate(topic, from_attributes=True)

@router.post("/{forum_id}/topics", response_model=TopicModel, dependencies=[require_login])
@requires("forum.topics.create")
def create_topic(
    request: Request,
    forum_id: int,
    data: TopicCreateRequest = Body(...)
) -> TopicModel:
    """
    Create a new topic in the specified forum.  
    Please note that the `icon` and `type` fields are only available to moderators!
    """
    if not (forum := forums.fetch_by_id(forum_id, request.state.db)):
        raise HTTPException(404, "The requested forum could not be found")
    
    if forum.hidden:
        raise HTTPException(404, "The requested forum could not be found")
    
    topic_attributes = {}

    if request.user.is_moderator and data.type:
        # Moderators can set the topic to be pinned or an announcement
        topic_attributes[data.type] = True

    can_change_icon = (
        request.user.is_moderator or
        request.user.is_bat or
        forum.allow_icons
    )

    if can_change_icon and data.icon:
        # Moderators, BATs, and forums that allow icons can set an icon
        topic_attributes['icon_id'] = data.icon

    topic = topics.create(
        forum.id,
        request.user.id,
        data.title,
        session=request.state.db,
        can_change_icon=forum.allow_icons,
        **topic_attributes
    )

    post = posts.create(
        topic.id,
        forum.id,
        request.user.id,
        data.content,
        session=request.state.db
    )

    update_notifications(
        data.notify,
        request.user.id,
        topic.id,
        session=request.state.db
    )

    broadcast_topic_activity(
        topic, post,
        request.user,
        request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} created a new topic "{topic.title}" ({topic.id}).'
    )

    return TopicModel.model_validate(topic, from_attributes=True)

def broadcast_topic_activity(
    topic: DBForumTopic,
    post: DBForumPost,
    author: DBUser,
    session: Session
) -> None:
    # Post to webhook & #announce channel
    activity.submit(
        author.id, None,
        UserActivity.ForumTopicCreated,
        {
            'username': author.name,
            'topic_name': topic.title,
            'forum_name': topic.forum.name,
            'forum_id': topic.forum_id,
            'topic_id': topic.id,
            'topic_icon': topic.icon.location if topic.icon else None,
            'content': post.content[:512] + ('...' if len(post.content) > 1024 else ''),
        },
        is_announcement=True,
        session=session
    )

def update_notifications(
    notify: bool,
    user_id: int,
    topic_id: int,
    session: Session
) -> None:
    if notify:
        topics.add_subscriber(
            topic_id,
            user_id,
            session=session
        )
        return

    topics.delete_subscriber(
        topic_id,
        user_id,
        session=session
    )
