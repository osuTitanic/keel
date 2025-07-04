
from app.models import ErrorResponse, FavouriteModel, UserModelCompact, BeatmapsetModel, FavouriteCreateRequest
from app.common.database import favourites, users, beatmapsets
from app.common.constants import UserActivity
from app.common.helpers import activity
from app.utils import requires

from fastapi import HTTPException, APIRouter, Request, Body
from typing import List

router = APIRouter(
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized action"},
        400: {"model": ErrorResponse, "description": "Bad request"}
    }
)

@router.get("/{user_id}/favourites", response_model=List[FavouriteModel])
def get_favourites(request: Request, user_id: int) -> List[FavouriteModel]:
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

@router.get("/{user_id}/favourites/{set_id}", response_model=FavouriteModel)
def get_favourite(request: Request, user_id: int, set_id: int) -> FavouriteModel:
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
@requires("beatmaps.favourites.create")
def add_favourite(
    request: Request,
    user_id: int,
    data: FavouriteCreateRequest = Body(...)
) -> FavouriteModel:
    if request.user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

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

    count = favourites.fetch_count(
        request.user.id,
        request.state.db
    )
    
    if count > 49:
        raise HTTPException(
            status_code=400,
            detail="You have too many favourite maps. Please go to your profile and delete some first."
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

    activity.submit(
        request.user.id, None,
        UserActivity.BeatmapFavouriteAdded,
        {
            'username': request.user.name,
            'beatmapset_id': beatmapset.id,
            'beatmapset_name': beatmapset.full_name
        },
        is_hidden=True,
        session=request.state.db
    )

    return FavouriteModel(
        user=UserModelCompact.model_validate(user, from_attributes=True),
        beatmapset=BeatmapsetModel.model_validate(beatmapset, from_attributes=True),
        created_at=favourite.created_at
    )

@router.delete("/{user_id}/favourites/{set_id}", response_model=FavouriteModel)
@requires("beatmaps.favourites.delete")
def remove_favourite(request: Request, user_id: int, set_id: int):
    if request.user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not (favourite := favourites.fetch_one(user.id, set_id, request.state.db)):
        raise HTTPException(
            status_code=400,
            detail="You have not favourited this beatmapset"
        )

    set_model = BeatmapsetModel.model_validate(favourite.beatmapset, from_attributes=True)
    user_model = UserModelCompact.model_validate(user, from_attributes=True)

    favourites.delete(
        user.id,
        favourite.set_id,
        request.state.db
    )

    activity.submit(
        request.user.id, None,
        UserActivity.BeatmapFavouriteRemoved,
        {
            'username': request.user.name,
            'beatmapset_id': favourite.beatmapset.id,
            'beatmapset_name': favourite.beatmapset.full_name
        },
        is_hidden=True,
        session=request.state.db
    )

    return FavouriteModel(
        user=user_model,
        beatmapset=set_model,
        created_at=favourite.created_at
    )
