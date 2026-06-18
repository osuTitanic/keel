
from fastapi import HTTPException, APIRouter, Request
from app.models import UserModel, StatsModel, ModeAlias
from app.common.database import users, stats

router = APIRouter()

@router.get("/{user_id}", response_model=UserModel)
def get_user_profile(request: Request, user_id: int) -> UserModel:
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

    return UserModel.model_validate(user, from_attributes=True)

@router.get("/{user_id}/stats")
def get_user_stats(request: Request, user_id: int):
    if not (user_stats := stats.fetch_all(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user stats could not be found"
        )

    user_stats.sort(
        key=lambda x: x.mode
    )
    return [
        StatsModel.model_validate(entry, from_attributes=True)
        for entry in user_stats
    ]

@router.get("/{user_id}/stats/{mode}")
def get_user_stats_by_mode(request: Request, user_id: int, mode: ModeAlias):
    if not (user_stats := stats.fetch_by_mode(user_id, mode.integer, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user stats could not be found"
        )

    return StatsModel.model_validate(user_stats, from_attributes=True)
