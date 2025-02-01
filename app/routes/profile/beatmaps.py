
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import RedirectResponse
from typing import List

from app.common.database import users, beatmapsets
from app.models import BeatmapsetModel

router = APIRouter()

@router.get('/{user_id}/beatmaps', response_model=List[BeatmapsetModel])
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

@router.get('/{user_id}/beatmaps/{beatmap_id}', response_model=BeatmapsetModel)
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
            f'/profile/{beatmapset.creator_id}/beatmaps/{beatmapset.id}',
            status_code=308
        )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
