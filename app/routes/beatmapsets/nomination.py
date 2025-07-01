
from fastapi import HTTPException, APIRouter, Request
from sqlalchemy.orm import Session
from typing import List

from app.common.database import notifications, beatmapsets, nominations, topics, posts
from app.common.constants import NotificationType, UserActivity
from app.models import NominationModel, ErrorResponse
from app.common.webhooks import Embed, Author, Image
from app.common.database import DBUser, DBBeatmapset
from app.common.helpers import activity
from app.security import require_login
from app.common import officer
from app.utils import requires

import config
import app

router = APIRouter()

responses = {
    401: {'model': ErrorResponse, 'description': 'Authentication failure'},
    404: {'model': ErrorResponse, 'description': 'Beatmapset not found'},
    400: {'model': ErrorResponse, 'description': 'Invalid request'}
}

@router.get("/{set_id}/nominations", response_model=List[NominationModel])
def beatmap_nominations(request: Request, set_id: int):
    return [
        NominationModel.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

@router.post("/{set_id}/nominations", response_model=List[NominationModel], dependencies=[require_login], responses=responses)
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

    # Set icon to bubble
    topics.update(
        beatmapset.topic_id,
        {
            'icon_id': 3,
            'forum_id': 9,
            'status_text': 'Waiting for approval...'
        },
        request.state.db
    )

    # Change to "ranked" forum
    posts.update_by_topic(
        beatmapset.topic_id,
        {'forum_id': 9},
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

    return [
        NominationModel.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

@router.delete("/{set_id}/nominations", response_model=List[NominationModel], dependencies=[require_login], responses=responses)
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

    nominations.delete_all(
        set_id,
        request.state.db
    )

    # Set icon to popped bubble
    topics.update(
        beatmapset.topic_id,
        {
            'forum_id': 10,
            'icon_id': 4,
            'status_text': 'Waiting for further modding...'
        },
        request.state.db
    )

    posts.update_by_topic(
        beatmapset.topic_id,
        {'forum_id': 10},
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
            NotificationType.Other,
            header=header,
            content=content,
            link=f'http://{config.DOMAIN_NAME}/s/{beatmapset.id}',
            session=request.state.db
        )
