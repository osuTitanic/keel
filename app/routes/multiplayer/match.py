
from fastapi import APIRouter, HTTPException, Request
from app.models import ErrorResponse, MatchModel
from app.common.database import matches

router = APIRouter(
    responses={404: {"description": "Match not found", "model": ErrorResponse}}
)

@router.get("", response_model=list[MatchModel])
def get_active_matches(request: Request) -> list[MatchModel]:
    return [
        MatchModel.model_validate(match, from_attributes=True)
        for match in matches.fetch_active(request.state.db)
    ]

@router.get("/{id}", response_model=MatchModel)
def get_match(request: Request, id: int) -> MatchModel:
    if not (match := matches.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404, detail="The requested match could not be found"
        )

    return MatchModel.model_validate(match, from_attributes=True)
