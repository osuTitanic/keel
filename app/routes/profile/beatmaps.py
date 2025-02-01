
from fastapi import HTTPException, APIRouter, Request
from app.common.database import users, beatmapsets
from app.models import BeatmapsetModel
from typing import List

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
