
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List

from app.common.database import users, beatmapsets, beatmaps, topics, posts
from app.common.constants import DatabaseStatus
from app.models import BeatmapsetModel
from app.utils import requires

router = APIRouter()

@router.get('/{user_id}/beatmapsets', response_model=List[BeatmapsetModel])
def get_user_beatmaps(request: Request, user_id: int) -> List[BeatmapsetModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user was not found'
        )
    
    user_beatmaps = beatmapsets.fetch_by_creator(
        user.id,
        request.state.db
    )

    return [
        BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
        for beatmapset in user_beatmaps
    ]

@router.get('/{user_id}/beatmapsets/{beatmap_id}', response_model=BeatmapsetModel)
def get_user_beatmap(request: Request, user_id: int, beatmap_id: int) -> BeatmapsetModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user was not found'
        )

    if not (beatmapset := beatmapsets.fetch_one(beatmap_id, request.state.db)):
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

    if beatmapset.creator_id != user.id:
        return RedirectResponse(
            f'/users/{beatmapset.creator_id}/beatmaps/{beatmapset.id}',
            status_code=308
        )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

@router.post('/{user_id}/beatmapsets/{beatmap_id}/revive')
@requires(['authenticated', 'activated'])
def revive_beatmapset(
    request: Request,
    user_id: int,
    beatmap_id: int
) -> BeatmapsetModel:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (beatmapset := beatmapsets.fetch_one(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )
    
    if beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if beatmapset.status != DatabaseStatus.Graveyard:
        raise HTTPException(
            status_code=400,
            detail="The requested beatmapset is not in the graveyard"
        )

    beatmapsets.update(
        beatmapset.id,
        {
            'status': DatabaseStatus.WIP.value,
            'last_update': datetime.now()
        },
        request.state.db
    )

    beatmaps.update_by_set_id(
        beatmapset.id,
        {
            'status': DatabaseStatus.WIP.value,
            'last_update': datetime.now()
        },
        request.state.db
    )

    topics.update(
        beatmapset.topic_id,
        {
            'forum_id': 10,
            'icon_id': None,
            'status_text': 'Needs modding'
        },
        request.state.db
    )

    posts.update_by_topic(
        beatmapset.topic_id,
        {'forum_id': 10},
        request.state.db
    )

    request.state.db.refresh(beatmapset)
    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
