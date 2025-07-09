
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from app.common.database import beatmaps
from app.models import ErrorResponse
from urllib.parse import quote

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Beatmap not found"}
    }
)

@router.get("/{id}/file", response_class=PlainTextResponse)
def get_beatmap_file(request: Request, id: int):
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if not (osu := request.state.storage.get_beatmap(id)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    return PlainTextResponse(
        content=osu,
        headers={'Content-Disposition': f'attachment; filename="{quote(beatmap.filename)}"'}
    )

@router.get("/{id}/background", response_class=Response)
def get_beatmap_background_large(request: Request, id: int):
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if not (file := request.state.storage.get_background(f'{beatmap.set_id}l')):
        raise HTTPException(404)

    return Response(
        file,
        media_type='image/jpeg'
    )

@router.get("/{id}/background/small", response_class=Response)
def get_beatmap_background_small(request: Request, id: int):
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if not (file := request.state.storage.get_background(f'{beatmap.set_id}')):
        raise HTTPException(404)

    return Response(
        file,
        media_type='image/jpeg'
    )
