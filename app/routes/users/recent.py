
from fastapi import HTTPException, Request, APIRouter, Query
from app.common.database import scores, users
from app.models import ScoreModel, ModeAlias
from typing import List

router = APIRouter()

@router.get("/{user_id}/recent", response_model=List[ScoreModel])
def get_recent_scores(
    request: Request,
    user_id: int,
    limit: int = Query(5, ge=1, le=50),
    min_status: int = Query(0, ge=0, le=3),
) -> List[ScoreModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    recent_scores = scores.fetch_recent_by_status(
        user.id,
        limit,
        min_status,
        request.state.db
    )

    return [
        ScoreModel.model_validate(score, from_attributes=True)
        for score in recent_scores
    ]

@router.get("/{user_id}/recent/{mode}", response_model=List[ScoreModel])
def get_recent_scores_by_mode(
    request: Request,
    user_id: int,
    mode: ModeAlias,
    limit: int = Query(5, ge=1, le=50),
    min_status: int = Query(0, ge=0, le=3),
) -> List[ScoreModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    recent_scores = scores.fetch_recent_by_status_and_mode(
        user.id,
        mode.integer,
        limit,
        min_status,
        request.state.db
    )

    return [
        ScoreModel.model_validate(score, from_attributes=True)
        for score in recent_scores
    ]
