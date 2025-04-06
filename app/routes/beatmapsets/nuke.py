

from fastapi import HTTPException, APIRouter, Request

from app.common.database import beatmapsets, topics, posts, beatmaps, modding
from app.models import BeatmapsetModel, ErrorResponse
from app.common.webhooks import Embed, Author, Image
from app.common.database import DBUser, DBBeatmapset
from app.common.constants import DatabaseStatus
from app.security import require_login
from app.common import officer
from app.utils import requires

import config
import app

router = APIRouter(
    dependencies=[require_login],
    responses={
        404: {'model': ErrorResponse, 'description': 'Beatmapset or topic not found'},
        401: {'model': ErrorResponse, 'description': 'Authentication failure'},
        400: {'model': ErrorResponse, 'description': 'Invalid request'}
    }
)

@router.post("/{set_id}/nuke", response_model=BeatmapsetModel)
@requires('bat')
def nuke_beatmap(request: Request, set_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, 'The requested beatmapset could not be found')

    if not beatmapset.topic_id:
        raise HTTPException(400, 'This beatmap does not have a forum topic')

    if beatmapset.status > 0:
        raise HTTPException(400, 'This beatmap has been approved and cannot be nuked')
    
    if not (topic := topics.fetch_one(beatmapset.topic_id, request.state.db)):
        raise HTTPException(404, 'The forum topic for this beatmap could not be found')
    
    topics.update(
        topic.id,
        {
            'icon_id': 7,
            'forum_id': 12,
            'status_text': None,
            'hidden': True
        },
        request.state.db
    )

    posts.update_by_topic(
        topic.id,
        {
            'forum_id': 12,
            'hidden': True
        },
        request.state.db
    )

    beatmapsets.update(
        set_id,
        {'status': DatabaseStatus.Inactive.value},
        request.state.db
    )

    beatmaps.update_by_set_id(
        set_id,
        {'status': DatabaseStatus.Inactive.value},
        request.state.db
    )

    modding.delete_by_set_id(
        set_id,
        request.state.db
    )

    request.state.storage.remove_osz2(beatmapset.id)
    request.state.storage.remove_osz(beatmapset.id)
    request.state.storage.remove_background(beatmapset.id)
    request.state.storage.remove_mp3(beatmapset.id)

    for beatmap in beatmapset.beatmaps:
        request.state.storage.remove_beatmap_file(beatmap.id)

    send_nuke_webhook(
        beatmapset,
        request.user
    )

    # TODO: Remove thumbnails, previews and osz files
    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'Beatmap "{beatmapset.full_name}" was nuked by {request.user.name}.'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def send_nuke_webhook(
    beatmapset: DBBeatmapset,
    user: DBUser
) -> None:
    embed = Embed(
        title=f'{beatmapset.artist} - {beatmapset.title}',
        url=f'http://osu.{config.DOMAIN_NAME}/s/{beatmapset.id}',
        thumbnail=Image(f'http://osu.{config.DOMAIN_NAME}/mt/{beatmapset.id}'),
        color=0xff0000
    )
    embed.author = Author(
        name=f'{user.name} nuked a Beatmap',
        url=f'http://osu.{config.DOMAIN_NAME}/u/{user.id}',
        icon_url=f'http://osu.{config.DOMAIN_NAME}/a/{user.id}'
    )
    officer.event(embeds=[embed])
