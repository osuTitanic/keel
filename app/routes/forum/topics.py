
from fastapi import HTTPException, APIRouter, Request, Query, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List

from app.common.database.objects import DBForumTopic, DBUser, DBForumPost
from app.models import TopicModel, ErrorResponse, TopicCreateRequest
from app.common.database import forums, topics, posts
from app.common.webhooks import Embed, Image, Author
from app.security import require_login
from app.common import officer
from app.utils import requires

import config

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

    send_topic_webhook(
        topic,
        post,
        request.user
    )

    request.state.logger.info(
        f'{request.user.name} created a new topic "{topic.title}" ({topic.id}).'
    )

    return TopicModel.model_validate(topic, from_attributes=True)

def send_topic_webhook(
    topic: DBForumTopic,
    post: DBForumPost,
    author: DBUser
) -> None:
    embed = Embed(
        title=topic.title,
        description=post.content[:512] + ('...' if len(post.content) > 1024 else ''),
        url=f'http://osu.{config.DOMAIN_NAME}/forum/{topic.forum_id}/t/{topic.id}',
        color=0xc4492e,
        thumbnail=(
            Image(f'https://osu.{config.DOMAIN_NAME}/{topic.icon.location}')
            if topic.icon else None
        )
    )
    embed.author = Author(
        name=f'{author.name} created a new Topic',
        url=f'http://osu.{config.DOMAIN_NAME}/u/{author.id}',
        icon_url=f'http://osu.{config.DOMAIN_NAME}/a/{author.id}'
    )
    officer.event(embeds=[embed])

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
