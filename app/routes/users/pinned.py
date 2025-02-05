
from fastapi import HTTPException, APIRouter, Request, Query, Body
from app.common.database import scores, users
from app.utils import requires
from app.models import (
    ScoreCollectionResponse,
    ScoreModelWithoutUser,
    ScorePinRequest,
    ErrorResponse,
    ModeAlias
)

router = APIRouter(
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized action"},
        400: {"model": ErrorResponse, "description": "Bad request"}
    }
)

@router.get("/{user_id}/pinned/{mode}", response_model=ScoreCollectionResponse)
def get_pinned_scores(
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

    pinned_scores = scores.fetch_pinned(
        user.id,
        mode.integer,
        limit=limit,
        offset=offset,
        session=request.state.db
    )

    pinned_count = scores.fetch_pinned_count(
        user.id,
        mode.integer,
        request.state.db
    )

    return ScoreCollectionResponse(
        total=pinned_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in pinned_scores
        ]
    )

@router.get("/{user_id}/pinned", response_model=ScoreCollectionResponse)
def get_pinned_scores_by_preferred_mode(
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

    pinned_scores = scores.fetch_pinned(
        user.id,
        user.preferred_mode,
        limit=limit,
        offset=offset,
        session=request.state.db
    )

    pinned_count = scores.fetch_pinned_count(
        user.id,
        user.preferred_mode,
        request.state.db
    )

    return ScoreCollectionResponse(
        total=pinned_count,
        scores=[
            ScoreModelWithoutUser.model_validate(score, from_attributes=True)
            for score in pinned_scores
        ]
    )

@router.post("/{user_id}/pinned", response_model=ScoreModelWithoutUser)
@requires("authenticated")
def pin_score(
    request: Request,
    user_id: int,
    data: ScorePinRequest = Body(...)
) -> ScoreModelWithoutUser:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to perform this action"
        )

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not (score := scores.fetch_by_id(data.score_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested score could not be found"
        )
    
    if score.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to perform this action"
        )
    
    if score.pinned:
        raise HTTPException(
            status_code=400,
            detail="The requested score is already pinned"
        )

    scores.update(
        score.id,
        {'pinned': True},
        request.state.db
    )

    return ScoreModelWithoutUser.model_validate(score, from_attributes=True)

@router.delete("/{user_id}/pinned", response_model=ScoreModelWithoutUser)
@requires("authenticated")
def unpin_score(
    request: Request,
    user_id: int,
    data: ScorePinRequest = Body(...)
) -> ScoreModelWithoutUser:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to perform this action"
        )

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not (score := scores.fetch_by_id(data.score_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested score could not be found"
        )

    if score.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to perform this action"
        )

    if not score.pinned:
        raise HTTPException(
            status_code=400,
            detail="The requested score was not pinned"
        )

    scores.update(
        score.id,
        {'pinned': False},
        request.state.db
    )

    return ScoreModelWithoutUser.model_validate(score, from_attributes=True)
