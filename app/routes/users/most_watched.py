
from fastapi import HTTPException, Request, APIRouter, Query
from app.models import ScoreCollectionResponse, ScoreModelWithoutUser, ModeAlias
from app.common.database import scores, users

router = APIRouter()

@router.get("/{user_id}/most-watched", response_model=ScoreCollectionResponse)
def get_most_watched_scores_preferred_mode(
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

    most_watched_scores = scores.fetch_most_watched_scores(
        user.id,
        user.preferred_mode,
        offset=offset,
        limit=limit,
        session=request.state.db
    )

    most_watched_count = scores.fetch_most_watched_scores_count(
        user.id,
        user.preferred_mode,
        session=request.state.db
    )

    return ScoreCollectionResponse(
        total=most_watched_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in most_watched_scores
        ]
    )

@router.get("/{user_id}/most-watched/{mode}", response_model=ScoreCollectionResponse)
def get_most_watched_scores(
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

    most_watched_scores = scores.fetch_most_watched_scores(
        user.id,
        mode.integer,
        offset=offset,
        limit=limit,
        session=request.state.db
    )

    most_watched_count = scores.fetch_most_watched_scores_count(
        user.id,
        mode.integer,
        session=request.state.db
    )

    return ScoreCollectionResponse(
        total=most_watched_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in most_watched_scores
        ]
    )
