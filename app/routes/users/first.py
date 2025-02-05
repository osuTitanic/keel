
from fastapi import HTTPException, APIRouter, Request, Query
from app.models import ScoreModelWithoutUser, ScoreCollectionResponse, ModeAlias
from app.common.database import scores, users

router = APIRouter()

@router.get("/{user_id}/first/{mode}", response_model=ScoreCollectionResponse)
def leader_scores(
    request: Request,
    user_id: int,
    mode: ModeAlias,
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

    first_scores = scores.fetch_leader_scores(
        user.id,
        mode.integer,
        offset=offset,
        limit=limit,
        session=request.state.db
    )

    first_count = scores.fetch_leader_count(
        user.id,
        mode.integer,
        request.state.db
    )

    return ScoreCollectionResponse(
        total=first_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in first_scores
        ]
    )

@router.get("/{user_id}/first", response_model=ScoreCollectionResponse)
def leader_scores_by_preferred_mode(
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

    first_scores = scores.fetch_leader_scores(
        user.id,
        user.preferred_mode,
        offset=offset,
        limit=limit,
        session=request.state.db
    )

    first_count = scores.fetch_leader_count(
        user.id,
        user.preferred_mode,
        request.state.db
    )

    return ScoreCollectionResponse(
        total=first_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in first_scores
        ]
    )
