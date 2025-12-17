
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import (
    HTTPException,
    APIRouter,
    Request,
    Query,
    Body
)

from app.common.constants import BeatmapStatus, NotificationType, UserActivity
from app.common.config import config_instance as config
from app.models import BeatmapsetModel, ErrorResponse
from app.common.database import DBBeatmapset, DBUser
from app.common.helpers import activity, permissions
from app.security import require_login
from app.utils import requires
from app.common.database import (
    notifications,
    nominations,
    beatmapsets,
    beatmaps,
    topics,
    scores,
    posts
)

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
    if status not in BeatmapStatus.values():
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
        status == BeatmapStatus.Ranked
        for status in status_updates.values()
    )

    if contains_ranked_status:
        if beatmapset.status not in (BeatmapStatus.Ranked, BeatmapStatus.Approved):
            raise HTTPException(
                status_code=400,
                detail="This beatmap is not yet ranked. Try to qualify it first!"
            )

        set_status = BeatmapStatus.Ranked.value

    contains_approved_status = any(
        status == BeatmapStatus.Approved
        for status in status_updates.values()
    )

    if contains_approved_status:
        if not has_enough_nominations(beatmapset, request.state.db):
            raise HTTPException(
                status_code=400,
                detail="This beatmap does not have enough nominations."
            )
        
        set_status = BeatmapStatus.Approved.value

    contains_qualified_status = any(
        status == BeatmapStatus.Qualified
        for status in status_updates.values()
    )

    if contains_qualified_status:
        if not has_enough_nominations(beatmapset, request.state.db):
            raise HTTPException(
                status_code=400,
                detail="This beatmap does not have enough nominations."
            )

        set_status = BeatmapStatus.Qualified.value

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

    broadcast_status_update(
        beatmapset,
        request.user,
        request.state.db
    )

    if set_status > BeatmapStatus.Pending:
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
        notify_nominatiors(
            f'Beatmap was disqualified',
            f'The beatmap "{beatmapset.full_name}" was disqualified by {request.user.name}.',
            beatmapset,
            request
        )

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
        BeatmapStatus.Pending.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': BeatmapStatus.Pending.value,
            'approved_at': None,
            'approved_by': None
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': BeatmapStatus.Pending.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        BeatmapStatus.Pending.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        BeatmapStatus.Pending.value,
        request.state.db
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'"{beatmapset.full_name}" was set to "Pending" status by {request.user.name}.'
    )

    broadcast_status_update(
        beatmapset,
        request.user,
        request.state.db
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def handle_approved_status(beatmapset: DBBeatmapset, request: Request) -> BeatmapsetModel:
    if not has_enough_nominations(beatmapset, request.state.db):
        raise HTTPException(
            status_code=400,
            detail="This beatmap does not have enough nominations."
        )

    is_allowed = permissions.has_permission(
        "beatmaps.moderation.force_approved",
        request.user.id,
    )

    if not is_allowed:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to force approve beatmaps."
        )

    update_beatmap_icon(
        beatmapset,
        BeatmapStatus.Approved.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': BeatmapStatus.Approved.value,
            'approved_at': datetime.now(),
            'approved_by': request.user.id
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': BeatmapStatus.Approved.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        BeatmapStatus.Approved.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        BeatmapStatus.Approved.value,
        request.state.db
    )

    broadcast_status_update(
        beatmapset,
        request.user,
        request.state.db
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
        BeatmapStatus.Qualified.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': BeatmapStatus.Qualified.value,
            'approved_at': datetime.now(),
            'approved_by': request.user.id
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': BeatmapStatus.Qualified.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        BeatmapStatus.Qualified.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        BeatmapStatus.Qualified.value,
        request.state.db
    )

    broadcast_status_update(
        beatmapset,
        request.user,
        request.state.db
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'"{beatmapset.full_name}" was set to "Qualified" status by {request.user.name}.'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

def handle_loved_status(beatmapset: DBBeatmapset, request: Request) -> BeatmapsetModel:
    update_beatmap_icon(
        beatmapset,
        BeatmapStatus.Loved.value,
        beatmapset.status,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': BeatmapStatus.Loved.value,
            'approved_at': datetime.now(),
            'approved_by': request.user.id
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': BeatmapStatus.Loved.value},
        request.state.db
    )

    move_beatmap_topic(
        beatmapset,
        BeatmapStatus.Loved.value,
        request.state.db
    )

    update_topic_status_text(
        beatmapset,
        BeatmapStatus.Loved.value,
        request.state.db
    )

    broadcast_status_update(
        beatmapset,
        request.user,
        request.state.db
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

def move_beatmap_topic(beatmapset: DBBeatmapset, status: BeatmapStatus, session: Session):
    if not beatmapset.topic_id:
        return

    forum_id = {
        BeatmapStatus.Pending: 9,
        BeatmapStatus.WIP: 10,
        BeatmapStatus.Graveyard: 12,
        BeatmapStatus.Approved: 8,
        BeatmapStatus.Qualified: 8,
        BeatmapStatus.Ranked: 8,
        BeatmapStatus.Loved: 8
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
    if status in (BeatmapStatus.Ranked, BeatmapStatus.Qualified, BeatmapStatus.Loved):
        # Set icon to heart
        topics.update(
            beatmapset.topic_id,
            {'icon_id': 1},
            session=session
        )
        return

    if status == BeatmapStatus.Approved:
        # Set icon to flame
        topics.update(
            beatmapset.topic_id,
            {'icon_id': 5},
            session=session
        )
        return

    ranked_statuses = (
        BeatmapStatus.Qualified,
        BeatmapStatus.Approved,
        BeatmapStatus.Ranked,
        BeatmapStatus.Loved
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

    if beatmapset.status > BeatmapStatus.Pending:
        topics.update(
            beatmapset.topic_id,
            {'status_text': None},
            session=session
        )

    elif status == BeatmapStatus.Graveyard:
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

def broadcast_status_update(
    beatmapset: DBBeatmapset,
    user: DBUser,
    session: Session
) -> None:
    # Post to webhook & #announce channel
    activity.submit(
        user.id, None,
        UserActivity.BeatmapStatusUpdated,
        {
            'username': user.name,
            'beatmapset_id': beatmapset.id,
            'beatmapset_name': beatmapset.full_name,
            'status': beatmapset.status,
            'beatmaps': {
                beatmap.version: beatmap.status
                for beatmap in beatmapset.beatmaps
            }
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
