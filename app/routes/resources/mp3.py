
from fastapi import HTTPException, APIRouter, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from app.common.database import beatmapsets
from app.security import require_login
from app.utils import requires
from io import BytesIO

router = APIRouter()

@router.get("/mp3/{filename}", response_class=StreamingResponse)
def get_internal_mp3(request: Request, filename: str):
    if not (file := request.state.storage.get_mp3_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        BytesIO(file),
        media_type="audio/mpeg"
    )

@router.put("/mp3/{set_id}", dependencies=[require_login])
@requires("beatmaps.resources.mp3.upload")
def upload_internal_background(
    request: Request,
    set_id: int,
    mp3: UploadFile = File(...)
) -> Response:
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap set could not be found"
        )

    request.state.storage.upload_mp3(
        beatmapset.id,
        mp3.file.read(),
    )

    return Response(
        status_code=204,
        headers={"Location": f'/resources/mp3/{beatmapset.id}'}
    )
