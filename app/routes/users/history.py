

from app.models import ModeAlias, RankHistoryModel, PlaysHistoryModel, ReplayHistoryModel
from app.common.database import histories, users
from fastapi import Request, HTTPException, APIRouter, Query
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.get("/{user_id}/history/rank/{mode}", response_model=List[RankHistoryModel])
def get_rank_history(
    request: Request,
    user_id: int,
    mode: ModeAlias,
    until: datetime = Query(None),
) -> List[RankHistoryModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    rank_history = histories.fetch_rank_history(
        user.id,
        mode.integer,
        until=until or datetime.now() - timedelta(days=90),
        session=request.state.db
    )

    return [
        RankHistoryModel.model_validate(rank, from_attributes=True)
        for rank in rank_history
    ]

@router.get("/{user_id}/history/plays/{mode}", response_model=List[PlaysHistoryModel])
def get_plays_history(
    request: Request,
    user_id: int,
    mode: ModeAlias,
    until: datetime = Query(None),
) -> List[PlaysHistoryModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    plays_history = histories.fetch_plays_history(
        user.id,
        mode.integer,
        until=until or datetime.now() - timedelta(days=90),
        session=request.state.db
    )

    return [
        PlaysHistoryModel.model_validate(play, from_attributes=True)
        for play in plays_history
    ]

@router.get("/{user_id}/history/views/{mode}", response_model=List[ReplayHistoryModel])
def get_replay_views_history(
    request: Request,
    user_id: int,
    mode: ModeAlias,
    until: datetime = Query(None),
) -> List[ReplayHistoryModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    replay_history = histories.fetch_replay_history(
        user.id,
        mode.integer,
        until=until or datetime.now() - timedelta(days=90),
        session=request.state.db
    )

    return [
        ReplayHistoryModel.model_validate(replay, from_attributes=True)
        for replay in replay_history
    ]
