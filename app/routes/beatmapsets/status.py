
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import (
    HTTPException,
    APIRouter,
    Request,
    Query,
    Body
)

from app.common.webhooks import Embed, Author, Image, Field
from app.models import BeatmapsetModel, ErrorResponse
from app.common.database import DBBeatmapset, DBUser
from app.common.constants import DatabaseStatus
from app.security import require_login
from app.common import officer
from app.utils import requires
from app.common.database import (
    nominations,
    beatmapsets,
    beatmaps,
    topics,
    scores,
    posts
)

import config

router = APIRouter(
    dependencies=[require_login],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failure"},
        404: {"model": ErrorResponse, "description": "Beatmapset not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"}
    }
)

@router.patch("/{set_id}/status", response_model=BeatmapsetModel)
@requires("beatmaps.update_status")
def update_beatmapset_status(
    request: Request,
    set_id: int,
    status: int = Query(...)
) -> BeatmapsetModel:
    if status not in DatabaseStatus.values():
        raise HTTPException(400, detail="Invalid status value")

    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, detail="The requested beatmapset could not be found")
    
    if beatmapset.status == status:
        return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

    status_handlers = {
        0: handle_pending_status,
        2: handle_approved_status,
        3: handle_qualified_status,
        4: handle_loved_status
    }

    if not (handler := status_handlers.get(status)):
        raise HTTPException(400)

    return handler(beatmapset, request)

@router.patch("/{set_id}/status/beatmaps", response_model=BeatmapsetModel)
@requires("beatmaps.update_status")
def update_beatmap_statuses(
    request: Request,
    set_id: int,
    updates: dict = Body(...)
) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404)
    
    status_updates = {
        int(key): int(value)
        for key, value in updates.items()
        if (key.isdecimal() and value.isdecimal()) and int(value) != -3
    }

    if not status_updates:
        return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
    
    set_status = max(status_updates.values())
    previous_status = beatmapset.status

    contains_ranked_status = any(
        status == DatabaseStatus.Ranked
        for status in status_updates.values()
    )

    if contains_ranked_status:
        if beatmapset.status not in (DatabaseStatus.Ranked, DatabaseStatus.Approved):
            raise HTTPException(
                status_code=400,
                detail="This beatmap is not yet ranked. Try to qualify it first!"
            )

        set_status = DatabaseStatus.Ranked.value

    contains_approved_status = any(
        status == DatabaseStatus.Approved
        for status in status_updates.values()
    )

    if contains_approved_status:
        if not has_enough_nominations(beatmapset, request.state.db):
            raise HTTPException(
                status_code=400,
                detail="This beatmap does not have enough nominations."
            )
        
        set_status = DatabaseStatus.Approved.value

    contains_qualified_status = any(
        status == DatabaseStatus.Qualified
        for status in status_updates.values()
    )

    if contains_qualified_status:
        if not has_enough_nominations(beatmapset, request.state.db):
            raise HTTPException(
                status_code=400,
                detail="This beatmap does not have enough nominations."
            )

        set_status = DatabaseStatus.Qualified.value

    for beatmap_id, status in status_updates.items():
        beatmaps.update(
            beatmap_id,
            {'status': status},
            request.state.db
        )

    beatmapsets.update(
        beatmapset.id,
        {'status': set_status},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        set_status,
        request.state.db
    )

    update_beatmap_icon(
        beatmapset,
        set_status,
        previous_status,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        set_status,
        request.state.db
    )

    send_status_webhook(
        beatmapset,
        request.user
    )

    if set_status > DatabaseStatus.Pending:
        beatmapsets.update(
            beatmapset.id,
            {
                'approved_at': datetime.now(),
                'approved_by': request.user.id
            },
            request.state.db
        )

    else:
        beatmapsets.update(
            beatmapset.id,
            {
                'approved_at': None,
                'approved_by': None
            },
            request.state.db
        )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'{request.user.name} updated statuses for "{beatmapset.full_name}".'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def handle_pending_status(beatmapset: DBBeatmapset, request: Request) -> BeatmapsetModel:
    if beatmapset.status > 0:
        nominations.delete_all(
            beatmapset.id,
            request.state.db
        )

        for beatmap in beatmapset.beatmaps:
            scores.delete_by_beatmap_id(
                beatmap.id,
                request.state.db
            )

    update_beatmap_icon(
        beatmapset,
        DatabaseStatus.Pending.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': DatabaseStatus.Pending.value,
            'approved_at': None,
            'approved_by': None
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': DatabaseStatus.Pending.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        DatabaseStatus.Pending.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        DatabaseStatus.Pending.value,
        request.state.db
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'"{beatmapset.full_name}" was set to "Pending" status by {request.user.name}.'
    )

    send_status_webhook(
        beatmapset,
        request.user
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def handle_approved_status(beatmapset: DBBeatmapset, request: Request) -> BeatmapsetModel:
    if not has_enough_nominations(beatmapset, request.state.db):
        raise HTTPException(
            status_code=400,
            detail="This beatmap does not have enough nominations."
        )

    update_beatmap_icon(
        beatmapset,
        DatabaseStatus.Approved.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': DatabaseStatus.Approved.value,
            'approved_at': datetime.now(),
            'approved_by': request.user.id
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': DatabaseStatus.Approved.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        DatabaseStatus.Approved.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        DatabaseStatus.Approved.value,
        request.state.db
    )

    send_status_webhook(
        beatmapset,
        request.user
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'"{beatmapset.full_name}" was set to "Approved" status by {request.user.name}.'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def handle_qualified_status(beatmapset: DBBeatmapset, request: Request) -> BeatmapsetModel:
    if not has_enough_nominations(beatmapset, request.state.db):
        raise HTTPException(
            status_code=400,
            detail="This beatmap does not have enough nominations."
        )

    update_beatmap_icon(
        beatmapset,
        DatabaseStatus.Qualified.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': DatabaseStatus.Qualified.value,
            'approved_at': datetime.now(),
            'approved_by': request.user.id
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': DatabaseStatus.Qualified.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        DatabaseStatus.Qualified.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        DatabaseStatus.Qualified.value,
        request.state.db
    )

    send_status_webhook(
        beatmapset,
        request.user
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'"{beatmapset.full_name}" was set to "Qualified" status by {request.user.name}.'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def handle_loved_status(beatmapset: DBBeatmapset, request: Request) -> BeatmapsetModel:
    update_beatmap_icon(
        beatmapset,
        DatabaseStatus.Loved.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': DatabaseStatus.Loved.value,
            'approved_at': datetime.now(),
            'approved_by': request.user.id
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': DatabaseStatus.Loved.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        DatabaseStatus.Loved.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        DatabaseStatus.Loved.value,
        request.state.db
    )

    send_status_webhook(
        beatmapset,
        request.user
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'"{beatmapset.full_name}" was set to "Loved" status by {request.user.name}.'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def required_nominations(beatmapset: DBBeatmapset) -> bool:
    beatmap_modes = len(
        set(
            beatmap.mode
            for beatmap in beatmapset.beatmaps
        )
    )

    # NOTE: Beatmap requires 2 approvals + 1 for each other mode
    additional_modes = beatmap_modes - 1
    return 2 + additional_modes

def has_enough_nominations(beatmapset: DBBeatmapset, session: Session) -> bool:
    count = nominations.count(
        beatmapset.id,
        session=session
    )

    return count >= required_nominations(beatmapset)

def move_beatmap_topic(beatmapset: DBBeatmapset, status: int, session: Session):
    if not beatmapset.topic_id:
        return

    forum_id = {
        DatabaseStatus.Pending: 9,
        DatabaseStatus.WIP: 10,
        DatabaseStatus.Graveyard: 12,
        DatabaseStatus.Approved: 8,
        DatabaseStatus.Qualified: 8,
        DatabaseStatus.Ranked: 8,
        DatabaseStatus.Loved: 8
    }.get(status, 9)

    topics.update(
        beatmapset.topic_id,
        {'forum_id': forum_id},
        session=session
    )
    posts.update_by_topic(
        beatmapset.topic_id,
        {'forum_id': forum_id},
        session=session
    )

def update_beatmap_icon(
    beatmapset: DBBeatmapset,
    status: int,
    previous_status: int,
    session: Session
) -> None:
    if status in (DatabaseStatus.Ranked, DatabaseStatus.Qualified, DatabaseStatus.Loved):
        # Set icon to heart
        topics.update(
            beatmapset.topic_id,
            {'icon_id': 1},
            session=session
        )
        return

    if status == DatabaseStatus.Approved:
        # Set icon to flame
        topics.update(
            beatmapset.topic_id,
            {'icon_id': 5},
            session=session
        )
        return

    ranked_statuses = (
        DatabaseStatus.Qualified,
        DatabaseStatus.Approved,
        DatabaseStatus.Ranked,
        DatabaseStatus.Loved
    )

    if previous_status in ranked_statuses:
        # Set icon to broken heart
        topics.update(
            beatmapset.topic_id,
            {'icon_id': 2},
            session=session
        )
        return

    # Remove icon
    topics.update(
        beatmapset.topic_id,
        {'icon_id': None},
        session=session
    )

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
        
        if not last_creator_post:
            topics.update(
                beatmapset.topic_id,
                {'status_text': 'Waiting for creator\'s response...'},
                session=session
            )
            return

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

def send_status_webhook(
    beatmapset: DBBeatmapset,
    user: DBUser
) -> None:
    embed = Embed(
        title=f'{beatmapset.artist} - {beatmapset.title}',
        url=f'http://osu.{config.DOMAIN_NAME}/s/{beatmapset.id}',
        thumbnail=Image(f'http://osu.{config.DOMAIN_NAME}/mt/{beatmapset.id}'),
        color=0x009ed9
    )

    embed.author = Author(
        name=f'{user.name} updated a beatmap',
        url=f'http://osu.{config.DOMAIN_NAME}/u/{user.id}',
        icon_url=f'http://osu.{config.DOMAIN_NAME}/a/{user.id}'
    )

    embed.fields= [
        Field(
            beatmap.version,
            f'{DatabaseStatus(beatmap.status).name}',
            inline=True
        )
        for beatmap in beatmapset.beatmaps
    ]

    officer.event(embeds=[embed])
