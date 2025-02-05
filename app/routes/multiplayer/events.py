
from fastapi import HTTPException, APIRouter, Request, Query
from datetime import datetime
from typing import List

from app.models import MatchEventModel, ErrorResponse
from app.common.database import matches, events

router = APIRouter(
    responses={404: {"description": "Match not found", "model": ErrorResponse}}
)

@router.get('/{id}/events', response_model=List[MatchEventModel])
def get_match_events(
    request: Request,
    id: int,
    after: datetime = Query(None)
) -> List[MatchEventModel]:
    if not (match := matches.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested match could not be found"
        )

    return [
        MatchEventModel.model_validate(event, from_attributes=True)
        for event in events.fetch_all_after_time(match.id, after or match.created_at, request.state.db)
    ]
