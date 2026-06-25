
from fastapi import HTTPException, APIRouter, Request
from app.models import BeatmapModelWithCollaborations, ErrorResponse
from app.common.database import beatmaps

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Beatmap not found"}
    }
)

@router.get("/{id}", response_model=BeatmapModelWithCollaborations)
def get_beatmap(request: Request, id: int) -> BeatmapModelWithCollaborations:
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

    return BeatmapModelWithCollaborations.model_validate(beatmap, from_attributes=True)
