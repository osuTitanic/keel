
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import StreamingResponse, Response
from app.common.database import beatmapsets
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={
        451: {"description": "Unavailable for legal reasons"},
        403: {'description': 'Authentication failure'},
        404: {"description": "Resource not found"},
    }
)

@router.get("/{id}/osz", dependencies=[require_login])
@requires("authenticated")
def get_osz(request: Request, id: int, no_video: bool = Query(False)) -> StreamingResponse:
    if not (beatmapset := beatmapsets.fetch_one(id, request.state.db)):
        raise HTTPException(status_code=404)

    if not beatmapset.available:
        raise HTTPException(status_code=451)

    if not (response := request.state.storage.api.osz(id, no_video)):
        raise HTTPException(404)

    return StreamingResponse(
        response.iter_content(1024*256),
        media_type='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename={id} {beatmapset.artist} - {beatmapset.title}.osz',
            'Content-Length': response.headers.get('Content-Length', 0)
        }
    )

@router.get("/{id}/background", response_class=Response)
def get_background_large(request: Request, id: int) -> Response:
    if not (file := request.state.storage.get_background(f'{id}l')):
        raise HTTPException(404)

    return Response(
        file,
        media_type='image/jpeg'
    )

@router.get("/{id}/background/small", response_class=Response)
def get_background_small(request: Request, id: int) -> Response:
    if not (file := request.state.storage.get_background(f'{id}')):
        raise HTTPException(404)

    return Response(
        file,
        media_type='image/jpeg'
    )

@router.get("/{id}/audio", response_class=Response)
def get_audio_preview(request: Request, id: int) -> Response:
    if not (file := request.state.storage.get_mp3(id)):
        raise HTTPException(404)

    return Response(
        file,
        media_type='audio/mpeg'
    )
