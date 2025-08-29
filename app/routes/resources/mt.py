
from fastapi import HTTPException, APIRouter, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from app.utils import requires, resize_image
from app.common.database import beatmapsets
from app.security import require_login
from datetime import timedelta
from io import BytesIO

router = APIRouter()

@router.get("/mt/{filename}", response_class=StreamingResponse)
def get_internal_background_large(request: Request, filename: str):
    if not (file := request.state.storage.get_background_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        BytesIO(file),
        media_type="image/jpeg",
        headers={"Content-Length": f"{len(file)}"}
    )

@router.get("/mt/{filename}/small", response_class=StreamingResponse)
def get_internal_background_small(request: Request, filename: str):
    if file := request.state.storage.get_from_cache(f'mt:{filename}'):
        return StreamingResponse(
            BytesIO(file),
            media_type="image/jpeg",
            headers={"Content-Length": f"{len(file)}"}
        )

    if not (file := request.state.storage.get_background_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    # Resize image into 80x60
    file_iterator = resize_image(file, 80, 60)

    # Save in cache
    request.state.storage.save_to_cache(
        name=f'mt:{filename}',
        content=file_iterator.getvalue(),
        expiry=timedelta(hours=6)
    )

    return StreamingResponse(
        file_iterator,
        media_type="image/jpeg",
        headers={"Content-Length": f"{len(file)}"}
    )

@router.put("/mt/{set_id}", dependencies=[require_login])
@requires("beatmaps.resources.mt.upload")
def upload_internal_background(
    request: Request,
    set_id: int,
    mt: UploadFile = File(...)
) -> Response:
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap set could not be found"
        )

    request.state.storage.upload_background(
        beatmapset.id,
        mt.file.read(),
    )

    return Response(
        status_code=204,
        headers={"Location": f'/resources/mt/{beatmapset.id}'}
    )
