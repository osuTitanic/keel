
from fastapi import Request, APIRouter, Query
from app.models import ScoreModel
from app.common.database import scores
from typing import List

router = APIRouter()

@router.get("/replays/most-viewed", response_model=List[ScoreModel])
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
