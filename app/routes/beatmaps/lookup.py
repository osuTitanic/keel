
from fastapi import HTTPException, APIRouter, Request
from app.common.database import DBBeatmap, beatmaps
from app.models import BeatmapModel, ErrorResponse

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Beatmap not found"}
    }
)

@router.get("/lookup/{query}", response_model=BeatmapModel)
def lookup_beatmap(request: Request, query: str) -> BeatmapModel:
    """
    Lookup a beatmap by it's filename or it's checksum,
    depending on the input that was provided.
    """
    if not (beatmap := resolve_beatmap(query, request)):
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

def resolve_beatmap(query: str, request: Request) -> DBBeatmap | None:
    if not query.endswith(".osu"):
        return beatmaps.fetch_by_checksum(query, request.state.db)

    return beatmaps.fetch_by_file(query, request.state.db)
