
from fastapi import HTTPException, APIRouter, Request
from app.models import BeatmapModel, ErrorResponse
from app.common.database import beatmaps

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "The requested beatmap could not be found"}
    }
)

@router.get("/{id}", response_model=BeatmapModel)
def get_beatmap(request: Request, id: int) -> BeatmapModel:
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )
    
    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )
    
    return BeatmapModel.model_validate(beatmap, from_attributes=True)
