
from fastapi import HTTPException, APIRouter, Request, Query, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.common.database.objects import DBForumTopic, DBUser, DBForumPost
from app.models import TopicModel, ErrorResponse, TopicCreateRequest, TopicUpdateRequest
from app.common.database import forums, topics, posts
from app.common.helpers import activity, permissions
from app.common.constants import UserActivity
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

    can_force_change_icon = permissions.has_permission(
        "forum.moderation.topics.change_icon",
        request.user.id
    )
    can_change_icon = (
        permissions.has_permission("forum.topics.change_icon", request.user.id) and
        forum.allow_icons
    )

    # BATs are able to change icons of topics that allow icon changes
    # Moderators can change icons regardless of forum settings
    can_change_icon = can_change_icon or can_force_change_icon

    # 'Attributes' refers to pinned/announcement status
    # which moderators and admins are allowed to set
    can_set_attributes = permissions.has_permission(
        "forum.moderation.topics.set_attributes",
        request.user.id
    )
    topic_attributes = {}

    if can_set_attributes and data.type:
        topic_attributes[data.type] = True

    if can_change_icon and data.icon:
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

@router.patch("/{forum_id}/topics/{topic_id}", response_model=TopicModel, dependencies=[require_login])
@requires("forum.topics.edit")
def update_topic(
    request: Request,
    forum_id: int,
    topic_id: int,
    data: TopicUpdateRequest = Body(...)
) -> TopicModel:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    if topic.forum_id != forum_id:
        return RedirectResponse(f"/forum/{topic.forum_id}/topics/{topic.id}")

    can_edit = permissions.has_permission(
        "forum.topics.edit",
        request.user.id
    )
    
    if not can_edit:
        raise HTTPException(403, "You do not have permission to edit topics")

    can_edit_others = permissions.has_permission(
        "forum.moderation.topics.edit",
        request.user.id
    )

    if topic.creator_id != request.user.id and not can_edit_others:
        raise HTTPException(403, "You do not have permission to edit this topic")

    if topic.locked_at and not can_edit_others:
        raise HTTPException(403, "This topic is locked and cannot be edited")

    can_lock_topic = permissions.has_permission(
        "forum.moderation.topics.lock",
        request.user.id
    )
    can_set_status = permissions.has_permission(
        "forum.moderation.topics.set_status",
        request.user.id
    )

    can_force_change_icon = permissions.has_permission(
        "forum.moderation.topics.change_icon",
        request.user.id
    )
    can_change_icon = (
        permissions.has_permission("forum.topics.change_icon", request.user.id) and
        topic.can_change_icon
    )

    # BATs are able to change icons of topics that allow icon changes
    # Moderators can change icons regardless of forum settings
    can_change_icon = can_change_icon or can_force_change_icon

    # 'Attributes' refers to pinned/announcement status
    # which moderators and admins are allowed to set
    can_set_attributes = permissions.has_permission(
        "forum.moderation.topics.set_attributes",
        request.user.id
    )

    updates = {}

    if data.title:
        updates['title'] = data.title

    if data.icon is not None and can_change_icon:
        updates['icon_id'] = data.icon if data.icon != -1 else None

    if data.type is not None and can_set_attributes:
        updates['pinned'] = data.type == 'pinned'
        updates['announcement'] = data.type == 'announcement'

    if data.status_text is not None and can_set_status:
        updates['status_text'] = data.status_text if data.status_text else None

    if data.lock_topic is not None and can_lock_topic:
        updates['locked_at'] = datetime.now() if not topic.locked_at else None

    if not updates:
        return TopicModel.model_validate(topic, from_attributes=True)

    topics.update(
        topic.id,
        updates,
        session=request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} updated topic "{topic.title}" ({topic.id}).'
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
