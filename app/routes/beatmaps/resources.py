
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from app.common.database import beatmaps
from app.models import ErrorResponse
from urllib.parse import quote

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Beatmap not found"}
    }
)

@router.get("/{id}/file")
def get_beatmap_file(request: Request, id: int):
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    osu = request.state.storage.get_beatmap(id)

    if not osu:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    return PlainTextResponse(
        content=osu,
        headers={'Content-Disposition': f'attachment; filename="{quote(beatmap.filename)}"'}
    )
