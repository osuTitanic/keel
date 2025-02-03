
from app.models import FavouriteModel, UserModelCompact, BeatmapsetModel
from app.common.database import favourites, users

from fastapi import HTTPException, APIRouter, Request
from typing import List

router = APIRouter()

@router.get("/{user_id}/favourites")
def get_favourites(request: Request, user_id: int) -> List[FavouriteModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    user_favourites = favourites.fetch_many(
        user.id,
        request.state.db
    )

    return [
        FavouriteModel(
            user=UserModelCompact.model_validate(user, from_attributes=True),
            beatmapset=BeatmapsetModel.model_validate(favourite.beatmapset, from_attributes=True),
            created_at=favourite.created_at
        )
        for favourite in user_favourites
    ]
