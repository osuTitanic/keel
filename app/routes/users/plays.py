
from fastapi import HTTPException, APIRouter, Request, Query
from typing import List

from app.common.database import plays, users
from app.models import BeatmapPlaysModel

router = APIRouter()

@router.get("/{user_id}/plays", response_model=List[BeatmapPlaysModel])
def get_most_played(
    request: Request,
    user_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=50)
) -> List[BeatmapPlaysModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    most_played = plays.fetch_most_played_by_user(
        user.id,
        limit,
        offset,
        session=request.state.db
    )

    return [
        BeatmapPlaysModel.model_validate(beatmap, from_attributes=True)
        for beatmap in most_played
    ]
