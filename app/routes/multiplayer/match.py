
from fastapi import HTTPException, APIRouter, Request
from app.common.database import matches
from app.models import MatchModel

router = APIRouter()

@router.get('/{id}', response_model=MatchModel)
def get_match(request: Request, id: int) -> MatchModel:
    if not (match := matches.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested match could not be found"
        )

    return MatchModel.model_validate(match, from_attributes=True)
