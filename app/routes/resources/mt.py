
from fastapi import HTTPException, APIRouter, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from .helpers import validate_beatmapset_for_upload

from app.common.storage.base import BaseStorage
from app.security import require_login
from app.utils import resize_image
from app.utils import requires
from datetime import timedelta
from io import BytesIO

router = APIRouter()

@router.get("/mt/{filename}", response_class=StreamingResponse)
def get_internal_background_large(request: Request, filename: str):
    if not (file := request.state.storage.get_background(filename)):
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
    if not (file := get_small_background(request.state.storage, filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        BytesIO(file),
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
    beatmapset = validate_beatmapset_for_upload(
        set_id,
        request.state.db
    )
    request.state.storage.upload_background(
        beatmapset.id,
        mt.file.read()
    )
    return Response(
        status_code=204,
        headers={"Location": f'/resources/mt/{beatmapset.id}'}
    )

def get_small_background(storage: BaseStorage, filename: str) -> bytes | None:
    if (cached := storage.get_from_cache(f'mt:{filename}')):
        return cached

    if not (large := storage.get_background(filename)):
        return None

    resized = resize_image(large, 80, 60).getvalue()
    storage.save_to_cache(
        name=f'mt:{filename}',
        content=resized,
        expiry=timedelta(hours=6)
    )
    return resized
