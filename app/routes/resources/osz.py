
from fastapi import HTTPException, APIRouter, Request, UploadFile, Query, File
from fastapi.responses import StreamingResponse, Response
from .helpers import validate_beatmapset_for_upload

from app.common.helpers.streaming import NoVideoZipIterator
from app.security import require_login
from app.utils import requires
from typing import Iterable
from io import BytesIO

router = APIRouter(
    responses={403: {'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get("/osz/{filename}", response_class=StreamingResponse)
def get_internal_osz(
    request: Request,
    filename: str,
    no_video: bool = Query(False)
) -> StreamingResponse:
    if not request.state.is_local_ip and 'beatmaps.download' not in request.auth.scopes:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not request.state.storage.file_exists(filename, 'osz'):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    generator, content_length = resolve_osz_iterator(
        filename, no_video, request
    )

    return StreamingResponse(
        generator,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}{"n" if no_video else ""}.osz"',
            "Content-Length": str(content_length)
        }
    )

@router.put("/osz/{set_id}")
@requires("beatmaps.resources.osz.upload")
def upload_internal_osz(
    request: Request,
    set_id: int,
    osz: UploadFile = File(...)
) -> Response:
    beatmapset = validate_beatmapset_for_upload(
        set_id,
        request.state.db,
        user_id=request.user.id,
        require_unranked=True,
    )

    request.state.storage.upload_osz(beatmapset.id, osz.file.read())

    return Response(
        status_code=204,
        headers={"Location": f'/resources/osz/{beatmapset.id}'}
    )

def resolve_osz_iterator(filename: str, no_video: bool, request: Request) -> Iterable:
    if not no_video:
        generator = request.state.storage.get_osz_iterable(filename)
        content_length = request.state.storage.get_osz_size(filename)
        return generator, content_length

    osz = request.state.storage.get_osz(filename)

    if not osz:
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    generator = NoVideoZipIterator(BytesIO(osz))
    content_length = len(generator)
    return generator, content_length
