
from fastapi import HTTPException, APIRouter, Request
from app.models import ScoreModel, ErrorResponse
from app.common.database import scores

router = APIRouter(
    responses={404: {"model": ErrorResponse, "description": "Score not found"}}
)

@router.get("/{score_id}", response_model=ScoreModel)
def get_score(request: Request, score_id: int):
    if not (score := scores.fetch_by_id(score_id, request.state.db)):
        raise HTTPException(404, "The requested score could not be found.")
    
    return ScoreModel.model_validate(score, from_attributes=True)
