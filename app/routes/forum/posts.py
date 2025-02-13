
from fastapi import HTTPException, APIRouter, Request, Query, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.common.database.objects import DBForumPost, DBForumTopic, DBBeatmapset, DBUser
from app.common.database import topics, posts, notifications, nominations, beatmapsets
from app.models import PostModel, ErrorResponse, PostCreateRequest, PostUpdateRequest
from app.common.constants import NotificationType, DatabaseStatus
from app.common.webhooks import Embed, Image, Author
from app.security import require_login
from app.common import officer
from app.utils import requires

import config

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

@router.post("/{forum_id}/topics/{topic_id}/posts", response_model=PostModel, dependencies=[require_login])
@requires(["authenticated", "activated", "unrestricted", "unsilenced"])
def create_post(
    request: Request,
    forum_id: int,
    topic_id: int,
    data: PostCreateRequest = Body(...)
) -> PostModel:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")
    
    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    if topic.forum_id != forum_id:
        return RedirectResponse(f"/forum/{topic.forum_id}/topics/{topic.id}/posts")
    
    new_icon = resolve_icon(
        data,
        request,
        topic
    )

    post = posts.create(
        topic.id,
        topic.forum_id,
        request.user.id,
        data.content,
        icon_id=new_icon,
        session=request.state.db
    )

    notify_subscribers(
        post,
        topic,
        session=request.state.db
    )

    update_notifications(
        data.notify,
        request.user.id,
        topic.id,
        session=request.state.db
    )

    topic_updates = {
        'last_post_at': datetime.now(),
        'icon_id': new_icon if new_icon else topic.icon_id
    }

    topics.update(
        topic.id,
        topic_updates,
        session=request.state.db
    )

    beatmapset = beatmapsets.fetch_by_topic(
        topic.id,
        request.state.db
    )

    if beatmapset:
        update_topic_status_text(
            beatmapset,
            beatmapset.status,
            request.state.db
        )

    send_post_webhook(
        topic,
        post,
        request.user
    )

    request.state.logger.info(
        f'{request.user.name} created a post on "{topic.title}" ({post.id}).'
    )

    return PostModel.model_validate(post, from_attributes=True)

@router.patch("/{forum_id}/topics/{topic_id}/posts/{post_id}", response_model=PostModel, dependencies=[require_login])
@requires(["authenticated", "activated"])
def edit_post(
    request: Request,
    forum_id: int,
    topic_id: int,
    post_id: int,
    data: PostUpdateRequest = Body(...)
) -> PostModel:
    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(404, "The requested post could not be found")

    if post.hidden:
        raise HTTPException(404, "The requested post could not be found")

    if post.topic_id != topic_id or post.forum_id != forum_id:
        return RedirectResponse(f"/forum/{post.forum_id}/topics/{post.topic_id}/posts/{post.id}")

    if post.edit_locked and not request.user.is_moderator:
        raise HTTPException(403, "This post is locked and cannot be edited")

    if post.topic.locked_at and not request.user.is_moderator:
        raise HTTPException(403, "This topic is locked and cannot be edited")

    if post.user_id != request.user.id and not request.user.is_moderator:
        raise HTTPException(403, "You are not authorized to perform this action")

    updates = {
        'content': data.content
    }

    if data.lock:
        updates['edit_locked'] = True

    if post.user_id == request.user.id:
        updates['edit_count'] = post.edit_count + 1
        updates['edit_time'] = datetime.now()

    posts.update(
        post.id,
        updates,
        request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} edited post "{post.id}" on "{post.topic.title}".'
    )

    return PostModel.model_validate(post, from_attributes=True)

def notify_subscribers(post: DBForumPost, topic: DBForumTopic, session: Session):
    subscribers = topics.fetch_subscribers(
        topic.id,
        session=session
    )

    for subscriber in subscribers:
        if subscriber.user_id == post.user_id:
            continue

        notifications.create(
            subscriber.user_id,
            NotificationType.News.value,
            f'New Post',
            f'{post.user.name} posted something in "{topic.title}". Click here to view it!',
            link=f'/forum/{topic.forum_id}/p/{post.id}',
            session=session
        )
        # TODO: Send email, based on preferences

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

def resolve_icon(data: PostCreateRequest, request: Request, topic: DBForumTopic) -> int | None:
    if data.icon is None:
        return

    is_privileged = (
        request.user.is_bat or
        request.user.is_moderator
    )

    if not topic.can_change_icon and not is_privileged:
        return

    if request.user.id != topic.creator_id and not is_privileged:
        return

    if topic.icon_id == data.icon:
        return

    if data.icon != -1:
        return data.icon

def send_post_webhook(
    topic: DBForumTopic,
    post: DBForumPost,
    author: DBUser
) -> None:
    embed = Embed(
        title=topic.title,
        description=post.content[:512] + ('...' if len(post.content) > 1024 else ''),
        url=f'http://osu.{config.DOMAIN_NAME}/forum/{topic.forum_id}/p/{post.id}',
        color=0xc4492e,
        thumbnail=(
            Image(f'https://osu.{config.DOMAIN_NAME}/{topic.icon.location}')
            if topic.icon else None
        )
    )
    embed.author = Author(
        name=f'{author.name} created a Post',
        url=f'http://osu.{config.DOMAIN_NAME}/u/{author.id}',
        icon_url=f'http://osu.{config.DOMAIN_NAME}/a/{author.id}'
    )
    officer.event(embeds=[embed])

def update_topic_status_text(
    beatmapset: DBBeatmapset,
    status: int,
    session: Session
) -> None:
    if not beatmapset.topic_id:
        return

    if beatmapset.status > DatabaseStatus.Pending:
        topics.update(
            beatmapset.topic_id,
            {'status_text': None},
            session=session
        )

    elif status == DatabaseStatus.Graveyard:
        topics.update(
            beatmapset.topic_id,
            {'status_text': None},
            session=session
        )

    else:
        beatmap_nominations = nominations.count(
            beatmapset.id,
            session=session
        )

        if beatmap_nominations > 0:
            topics.update(
                beatmapset.topic_id,
                {'status_text': 'Waiting for approval...'},
                session=session
            )
            return

        last_bat_post = posts.fetch_last_bat_post(
            beatmapset.topic_id,
            session=session
        )

        if not last_bat_post:
            topics.update(
                beatmapset.topic_id,
                {'status_text': 'Needs modding'},
                session=session
            )
            return

        last_creator_post = posts.fetch_last_by_user(
            beatmapset.topic_id,
            beatmapset.creator_id,
            session=session
        )

        if last_bat_post.id > last_creator_post.id:
            topics.update(
               beatmapset.topic_id,
                {'status_text': "Waiting for creator's response..."},
                session=session
            )
            return

        topics.update(
            beatmapset.topic_id,
            {'status_text': 'Waiting for further modding...'},
            session=session
        )
