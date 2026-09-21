
from fastapi import HTTPException, APIRouter, Request
from sqlalchemy.orm import Session
from typing import List

from app.common.database import notifications, beatmapsets, nominations, topics, posts, users
from app.common.constants import NotificationType, UserActivity
from app.models import NominationModelWithUser, ErrorResponse
from app.common.config import config_instance as config
from app.common.database import DBUser, DBBeatmapset
from app.common.helpers import activity
from app.security import require_login
from app.utils import requires

router = APIRouter()

responses = {
    401: {'model': ErrorResponse, 'description': 'Authentication failure'},
    404: {'model': ErrorResponse, 'description': 'Beatmapset not found'},
    400: {'model': ErrorResponse, 'description': 'Invalid request'}
}

@router.get("/{set_id}/nominations", response_model=List[NominationModelWithUser])
def beatmap_nominations(request: Request, set_id: int):
    return [
        NominationModelWithUser.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

@router.post("/{set_id}/nominations", response_model=List[NominationModelWithUser], dependencies=[require_login], responses=responses)
@requires("beatmaps.nominations.create")
def nominate_beatmap(request: Request, set_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, "The requested beatmapset could not be found")

    if beatmapset.status > 0:
        raise HTTPException(400, "This beatmap is already in approved status")

    if beatmapset.creator_id == request.user.id:
        raise HTTPException(400, "You cannot nominate your own beatmap")

    if nominations.fetch_one(set_id, request.user.id, request.state.db):
        raise HTTPException(400, "You have already nominated this beatmap")

    nominations.create(
        beatmapset.id,
        request.user.id,
        request.state.db
    )

    can_move_topic = can_automove_topic(
        beatmapset,
        request
    )
    topic_updates = {
        'icon_id': 3, # Set icon to bubble
        'status_text': 'Waiting for approval...'
    }
    if can_move_topic:
        topic_updates['forum_id'] = 9 # Switch to pending forum

    topics.update(
        beatmapset.topic_id,
        topic_updates,
        request.state.db
    )

    if can_move_topic:
        posts.update_by_topic(
            beatmapset.topic_id,
            {'forum_id': 9}, # Switch to pending forum, if allowed
            request.state.db
        )

    broadcast_nomination(
        beatmapset,
        request.user,
        type='add',
        session=request.state.db
    )

    request.state.logger.info(
        f'Beatmap "{beatmapset.full_name}" was nominated by {request.user.name}.'
    )
    request.state.db.commit()

    return [
        NominationModelWithUser.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

@router.delete("/{set_id}/nominations", response_model=List[NominationModelWithUser], dependencies=[require_login], responses=responses)
@requires("beatmaps.nominations.delete")
def reset_nominations(request: Request, set_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, "The requested beatmap could not be found")

    if beatmapset.status > 0:
        raise HTTPException(400, "This beatmap is already in approved status")

    if beatmapset.creator_id == request.user.id:
        raise HTTPException(400, "You cannot reset your own beatmap")

    notify_nominatiors(
        'Bubble popped',
        f'The nominations for "{beatmapset.full_name}" have been reset by {request.user.name}.',
        beatmapset,
        request
    )

    deleted_nominations = nominations.delete_all(
        set_id,
        request.state.db
    )
    if deleted_nominations == 0:
        raise HTTPException(400, "This beatmap has no nominations to reset")

    beatmapsets.update(
        beatmapset.id,
        {'star_priority': beatmapset.star_priority + 5},
        request.state.db
    )

    can_move_topic = can_automove_topic(
        beatmapset,
        request
    )
    topic_updates = {
        'icon_id': 4, # Set icon to popped bubble
        'status_text': 'Waiting for further modding...'
    }
    if can_move_topic:
        topic_updates['forum_id'] = 10 # Set forum to WIP
    
    topics.update(
        beatmapset.topic_id,
        topic_updates,
        request.state.db
    )
    if can_move_topic:
        posts.update_by_topic(
            beatmapset.topic_id,
            {'forum_id': 10}, # Switch to WIP forum, if allowed
            request.state.db
        )

    broadcast_nomination(
        beatmapset,
        request.user,
        type='reset',
        session=request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} removed all nominations from "{beatmapset.full_name}".'
    )
    return []

@router.post("/{set_id}/nominations/{user_id}", response_model=List[NominationModelWithUser], dependencies=[require_login], responses=responses)
@requires("beatmaps.moderation.force_nominate")
def force_nominate(request: Request, set_id: int, user_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, "The requested beatmapset could not be found")

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "The specified user could not be found")

    if nominations.fetch_one(set_id, user_id, request.state.db):
        raise HTTPException(400, "This user has already nominated this beatmap")

    nominations.create(
        beatmapset.id,
        user_id,
        request.state.db
    )

    request.state.logger.info(
        f'Beatmap "{beatmapset.full_name}" was force-nominated by {request.user.name} for {user.name}.'
    )
    request.state.db.commit()

    return [
        NominationModelWithUser.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

@router.delete("/{set_id}/nominations/{user_id}", response_model=List[NominationModelWithUser], dependencies=[require_login], responses=responses)
@requires("beatmaps.moderation.force_nominate")
def force_remove_nomination(request: Request, set_id: int, user_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, "The requested beatmapset could not be found")

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "The specified user could not be found")

    if not nominations.fetch_one(set_id, user_id, request.state.db):
        raise HTTPException(400, "This user has not nominated this beatmap")

    nominations.delete(
        set_id,
        user_id,
        request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} removed the nomination of {user.name} from "{beatmapset.full_name}".'
    )
    request.state.db.commit()

    return [
        NominationModelWithUser.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

def broadcast_nomination(
    beatmapset: DBBeatmapset,
    user: DBUser,
    type: str,
    session: Session
) -> None:
    # Post to webhook & #announce channel
    activity.submit(
        user.id, None,
        UserActivity.BeatmapNominated,
        {
            'username': user.name,
            'beatmapset_id': beatmapset.id,
            'beatmapset_name': beatmapset.full_name,
            'type': type
        },
        is_announcement=True,
        session=session
    )

def notify_nominatiors(
    header: str,
    content: str,
    beatmapset: DBBeatmapset,
    request: Request,
) -> None:
    entries = nominations.fetch_by_beatmapset(
        beatmapset.id,
        request.state.db
    )

    for nomination in entries:
        if nomination.user_id == request.user.id:
            continue

        notifications.create(
            nomination.user_id,
            NotificationType.Beatmaps,
            header=header,
            content=content,
            link=f'http://{config.DOMAIN_NAME}/s/{beatmapset.id}',
            session=request.state.db
        )

def can_automove_topic(beatmapset: DBBeatmapset, request: Request):
    topic = topics.fetch_one(
        beatmapset.topic_id,
        session=request.state.db
    )
    return (
        topic is not None
        and beatmapset.server == 1
        and topic.forum_id in (8, 9, 10, 12)
    )
