
from fastapi import HTTPException, APIRouter, Request, Query
from app.models import ScoreModel, ErrorResponse
from app.common.database import scores
from typing import List

router = APIRouter(
    responses={404: {"model": ErrorResponse, "description": "Score not found"}}
)

@router.get("/most-viewed", response_model=List[ScoreModel])
def get_most_viewed_replays(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> List[ScoreModel]:
    most_viewed = scores.fetch_most_viewed(
        limit=limit,
        offset=offset,
        session=request.state.db
    )

    return [
        ScoreModel.model_validate(score, from_attributes=True)
        for score in most_viewed
    ]

@router.get("/{score_id}", response_model=ScoreModel)
def get_score(request: Request, score_id: int):
    if not (score := scores.fetch_by_id(score_id, request.state.db)):
        raise HTTPException(404, "The requested score could not be found.")

    return ScoreModel.model_validate(score, from_attributes=True)
