
from fastapi import HTTPException, APIRouter, Request, Query
from app.models import ScoreCollectionResponse, ScoreModelWithoutUser, ModeAlias
from app.common.database.repositories import scores, users
from typing import List

router = APIRouter()

@router.get('/{user_id}/pinned/{mode}', response_model=ScoreCollectionResponse)
def pinned_scores(
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
            detail="The requested user was not found"
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
