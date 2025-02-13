
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/osu/{filename}", response_class=PlainTextResponse)
def get_internal_beatmap(request: Request, filename: str):
    if not (file := request.state.storage.get_beatmap_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return PlainTextResponse(
        file,
        media_type="text/plain"
    )
