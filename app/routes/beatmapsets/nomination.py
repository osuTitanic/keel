
from __future__ import annotations
from fastapi import APIRouter, Request
from typing import List

from app.common.database import beatmapsets, nominations, topics, posts
from app.common.webhooks import Embed, Author, Image
from app.common.database import DBUser, DBBeatmapset
from app.models import UserModel, NominationModel
from app.common import officer

import config
import app

router = APIRouter()

@router.get('/{set_id}/nominations', response_model=List[NominationModel])
def get_nominations(request: Request, set_id: int):
    return [
        NominationModel.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]

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
