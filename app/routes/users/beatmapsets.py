
from fastapi import HTTPException, APIRouter, Request, Body
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List

from app.models import BeatmapsetModel, ErrorResponse, BeatmapsetDescriptionUpdate
from app.common.database import users, beatmapsets, beatmaps, topics, posts, nominations
from app.common.constants import BeatmapStatus, UserActivity
from app.utils import requires, primary_beatmapset_mode
from app.common.helpers import activity

router = APIRouter()
action_responses = {
    403: {"model": ErrorResponse, "description": "Unauthorized action"},
    400: {"model": ErrorResponse, "description": "Bad request"}
}

@router.get("/{user_id}/beatmapsets", response_model=List[BeatmapsetModel])
def get_user_beatmapsets(request: Request, user_id: int) -> List[BeatmapsetModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )
    
    user_beatmaps = beatmapsets.fetch_by_creator(
        user.id,
        request.state.db
    )

    return [
        BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
        for beatmapset in user_beatmaps
        if beatmapset.status != BeatmapStatus.Inactive
    ]

@router.get("/{user_id}/beatmapsets/{beatmapset_id}", response_model=BeatmapsetModel)
def get_user_beatmapset(request: Request, user_id: int, beatmapset_id: int) -> BeatmapsetModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )

    if not (beatmapset := beatmapsets.fetch_one(beatmapset_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if beatmapset.server != 1:
        # Beatmap was not uploaded on titanic
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if beatmapset.status == BeatmapStatus.Inactive:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if beatmapset.creator_id != user.id:
        return RedirectResponse(
            f'/users/{beatmapset.creator_id}/beatmaps/{beatmapset.id}',
            status_code=308
        )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

@router.post("/{user_id}/beatmapsets/{beatmapset_id}/revive", response_model=BeatmapsetModel, responses=action_responses)
@requires("beatmaps.revive")
def revive_beatmapset(
    request: Request,
    user_id: int,
    beatmapset_id: int
) -> BeatmapsetModel:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (beatmapset := beatmapsets.fetch_one(beatmapset_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )
    
    if beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if beatmapset.status != BeatmapStatus.Graveyard:
        raise HTTPException(
            status_code=400,
            detail="The requested beatmapset is not in the graveyard"
        )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': BeatmapStatus.WIP.value,
            'last_update': datetime.now()
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {
            'status': BeatmapStatus.WIP.value,
            'last_update': datetime.now()
        },
        request.state.db
    )

    topics.update(
        beatmapset.topic_id,
        {
            'status_text': 'Needs modding',
            'icon_id': None,
            'hidden': False,
            'forum_id': 10
        },
        request.state.db
    )

    posts.update_by_topic(
        beatmapset.topic_id,
        {
            'hidden': False,
            'forum_id': 10
        },
        request.state.db
    )

    activity.submit(
        beatmapset.creator_id,
        primary_beatmapset_mode(beatmapset.beatmaps),
        UserActivity.BeatmapRevived,
        {
            "username": beatmapset.creator,
            "beatmapset_id": beatmapset.id,
            "beatmapset_name": beatmapset.full_name
        },
        is_announcement=True,
        session=request.state.db
    )

    request.state.db.refresh(beatmapset)
    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

@router.patch("/{user_id}/beatmapsets/{beatmapset_id}/description", response_model=BeatmapsetModel, responses=action_responses)
@requires("beatmaps.upload")
def update_beatmapset_description(
    request: Request,
    user_id: int,
    beatmapset_id: int,
    update: BeatmapsetDescriptionUpdate = Body(...)
) -> BeatmapsetModel:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (beatmapset := beatmapsets.fetch_one(beatmapset_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    beatmapsets.update(
        beatmapset.id,
        {'description': update.bbcode},
        request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} updated description for "{beatmapset.full_name}".'
    )

    beatmap_topic = topics.fetch_one(
        beatmapset.topic_id,
        session=request.state.db
    )

    if not beatmap_topic:
        return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

    initial_post = posts.fetch_initial_post(
        beatmap_topic.id,
        session=request.state.db
    )

    if not initial_post:
        return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

    if '---------------' not in initial_post.content.splitlines():
        raise HTTPException(
            status_code=400,
            detail="Invalid post format"
        )

    metadata, _ = initial_post.content.split('---------------', 1)

    # Update forum topic content with new description
    posts.update(
        initial_post.id,
        {'content': f'{metadata}---------------\n{update.bbcode}'},
        session=request.state.db
    )

    request.state.db.refresh(beatmapset)
    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

@router.delete("/{user_id}/beatmapsets/{beatmapset_id}", response_model=BeatmapsetModel, responses=action_responses)
@requires("beatmaps.delete")
def delete_beatmapset(
    request: Request,
    user_id: int,
    beatmapset_id: int
) -> BeatmapsetModel:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (beatmapset := beatmapsets.fetch_one(beatmapset_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )
    
    if beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if beatmapset.status > 0:
        raise HTTPException(
            status_code=400,
            detail="The requested beatmapset cannot be deleted"
        )

    has_nomination = nominations.fetch_by_beatmapset(
        beatmapset.id,
        request.state.db
    )

    if has_nomination:
        raise HTTPException(
            status_code=400,
            detail="The requested beatmapset was nominated, and cannot be deleted"
        )

    # Beatmap will be deleted on next bss upload
    beatmapsets.update(
        beatmapset.id,
        {'status': BeatmapStatus.Inactive.value},
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {'status': BeatmapStatus.Inactive.value},
        request.state.db
    )

    topics.update(
        beatmapset.topic_id,
        {'hidden': True},
        request.state.db
    )

    posts.update_by_topic(
        beatmapset.topic_id,
        {'hidden': True},
        request.state.db
    )

    request.state.db.refresh(beatmapset)
    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
