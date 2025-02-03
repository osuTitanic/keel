
from app.models import FavouriteModel, UserModelCompact, BeatmapsetModel, FavouriteCreateRequest
from app.common.database import favourites, users, beatmapsets

from fastapi import HTTPException, APIRouter, Request, Body
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

@router.get("/{user_id}/favourites/{set_id}")
def get_favourite(request: Request, user_id: int, set_id: int) -> FavouriteModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not (favourite := favourites.fetch_one(user.id, set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="You have not favourited this beatmapset"
        )

    return FavouriteModel(
        user=UserModelCompact.model_validate(user, from_attributes=True),
        beatmapset=BeatmapsetModel.model_validate(favourite.beatmapset, from_attributes=True),
        created_at=favourite.created_at
    )

@router.post("/{user_id}/favourites", response_model=FavouriteModel)
def add_favourite(
    request: Request,
    user_id: int,
    data: FavouriteCreateRequest = Body(...)
) -> FavouriteModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )
    
    if not (beatmapset := beatmapsets.fetch_one(data.set_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    already_exists = favourites.fetch_one(
        request.user.id,
        beatmapset.id,
        request.state.db
    )

    if already_exists:
        raise HTTPException(
            status_code=400,
            detail="You have already favourited this beatmapset"
        )

    favourite = favourites.create(
        request.user.id,
        beatmapset.id,
        request.state.db
    )

    if not favourite:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while trying to add the favourite"
        )
    
    return FavouriteModel(
        user=UserModelCompact.model_validate(user, from_attributes=True),
        beatmapset=BeatmapsetModel.model_validate(beatmapset, from_attributes=True),
        created_at=favourite.created_at
    )

@router.delete("/{user_id}/favourites/{set_id}", response_model=FavouriteModel)
def remove_favourite(request: Request, user_id: int, set_id: int):
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not (favourite := favourites.fetch_one(user.id, set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="You have not favourited this beatmapset"
        )

    set_model = BeatmapsetModel.model_validate(favourite.beatmapset, from_attributes=True)
    user_model = UserModelCompact.model_validate(user, from_attributes=True)

    favourites.delete(
        user.id,
        favourite.set_id,
        request.state.db
    )

    return FavouriteModel(
        user=user_model,
        beatmapset=set_model,
        created_at=favourite.created_at
    )
