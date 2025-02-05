
from fastapi import HTTPException, APIRouter, Request
from typing import List

from app.common.database import beatmapsets, nominations, topics, posts
from app.models import NominationModel, ErrorResponse
from app.common.webhooks import Embed, Author, Image
from app.common.database import DBUser, DBBeatmapset
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
@requires("bat")
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

    send_nomination_webhook(
        beatmapset,
        request.user,
        type='add'
    )

    request.state.logger.info(
        f'Beatmap "{beatmapset.full_name}" was nominated by {request.user.name}.'
    )

    return [
        NominationModel.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

@router.delete("/{set_id}/nominations", response_model=List[NominationModel], dependencies=[require_login], responses=responses)
@requires("bat")
def reset_nominations(request: Request, set_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, "The requested beatmap could not be found")
    
    if beatmapset.status > 0:
        raise HTTPException(400, "This beatmap is already in approved status")
    
    if beatmapset.creator_id == request.user.id:
        raise HTTPException(400, "You cannot reset your own beatmap")
    
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

    send_nomination_webhook(
        beatmapset,
        request.user,
        type='reset'
    )

    request.state.logger.info(
        f'{request.user.name} removed all nominations from "{beatmapset.full_name}".'
    )

    return []

def send_nomination_webhook(
    beatmapset: DBBeatmapset,
    user: DBUser,
    type: str = 'add'
) -> None:
    author_text = {
        'add': f'{user.name} nominated a Beatmap',
        'reset': f'{user.name} reset all nominations',
    }
    color = {
        'add': 0x00da1d,
        'reset': 0xff0000,
    }
    embed = Embed(
        title=f'{beatmapset.artist} - {beatmapset.title}',
        url=f'http://osu.{config.DOMAIN_NAME}/s/{beatmapset.id}',
        thumbnail=Image(f'http://osu.{config.DOMAIN_NAME}/mt/{beatmapset.id}'),
        color=color.get(type)
    )
    embed.author = Author(
        name=author_text.get(type),
        url=f'http://osu.{config.DOMAIN_NAME}/u/{user.id}',
        icon_url=f'http://osu.{config.DOMAIN_NAME}/a/{user.id}'
    )
    officer.event(embeds=[embed])
