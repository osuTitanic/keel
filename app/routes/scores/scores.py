
from fastapi import HTTPException, APIRouter, Request
from app.common.database import scores
from app.models import ScoreModel

router = APIRouter()

@router.get('/{score_id}', response_model=ScoreModel)
def get_score(request: Request, score_id: int):
    if not (score := scores.fetch_by_id(score_id, request.state.db)):
        raise HTTPException(404, "The requested score was not found.")
    
    return ScoreModel.model_validate(score, from_attributes=True)
