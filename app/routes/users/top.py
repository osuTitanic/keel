
from app.models import ScoreCollectionResponse, ScoreModelWithoutUser, ModeAlias
from app.common.database.repositories import scores, users
from fastapi import HTTPException, Request, APIRouter, Query
from config import APPROVED_MAP_REWARDS

router = APIRouter()

@router.get("/{user_id}/top", response_model=ScoreCollectionResponse)
def get_top_plays_preferred_mode(
    request: Request,
    user_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> ScoreCollectionResponse:
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

    top_scores = scores.fetch_top_scores(
        user.id,
        user.preferred_mode,
        offset=offset,
        limit=limit,
        exclude_approved=(not APPROVED_MAP_REWARDS),
        session=request.state.db
    )

    top_count = scores.fetch_top_scores_count(
        user.id,
        user.preferred_mode,
        request.state.db
    )

    return ScoreCollectionResponse(
        total=top_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in top_scores
        ]
    )

@router.get("/{user_id}/top/{mode}", response_model=ScoreCollectionResponse)
def get_top_plays(
    request: Request,
    mode: ModeAlias,
    user_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> ScoreCollectionResponse:
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

    top_scores = scores.fetch_top_scores(
        user.id,
        mode.integer,
        offset=offset,
        limit=limit,
        session=request.state.db
    )

    top_count = scores.fetch_top_scores_count(
        user.id,
        mode.integer,
        request.state.db
    )

    return ScoreCollectionResponse(
        total=top_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in top_scores
        ]
    )
