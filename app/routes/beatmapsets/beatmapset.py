
from fastapi import HTTPException, APIRouter, Request
from app.models import BeatmapsetModel, ErrorResponse
from app.common.database import beatmapsets

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "The requested beatmap could not be found"}
    }
)

@router.get("/{id}", response_model=BeatmapsetModel)
def get_beatmapset(request: Request, id: int) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmapset.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
