
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from app.models import ErrorResponse

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "The requested beatmap could not be found"}
    }
)

@router.get('/{id}/file')
def internal_beatmap_file(request: Request, id: int):
    osu = request.state.storage.get_beatmap_internal(id)

    if not osu:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    return PlainTextResponse(
        content=osu,
        headers={'Content-Disposition': f'attachment; filename={id}.osu'}
    )
