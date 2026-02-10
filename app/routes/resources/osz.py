
from fastapi import HTTPException, APIRouter, Request, UploadFile, Query, File
from fastapi.responses import StreamingResponse, Response

from app.streaming import NoVideoZipIterator, ZipIterator
from app.common.database import beatmapsets
from app.common.helpers import permissions
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={403: {'description': 'Authentication failure'}},
    dependencies=[require_login]
)
video_file_extensions = frozenset((
    ".wmv", ".flv", ".mp4",
    ".avi", ".m4v", ".mpg",
    ".mov", ".webm", ".mkv",
    ".ogv", ".mpeg", ".3gp"
))

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

    if request.state.storage.config.S3_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="S3 storage is currently not implemented"
        )

    if not request.state.storage.file_exists(filename, 'osz'):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    if not (filepath := request.state.storage.get_osz_internal_path(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    iterator_class = (
        NoVideoZipIterator if no_video else
        ZipIterator
    )
    generator = iterator_class(filepath)

    return StreamingResponse(
        generator,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}{"n" if no_video else ""}.osz"',
            "Content-Length": str(len(generator))
        }
    )

@router.put("/osz/{set_id}")
@requires("beatmaps.resources.osz.upload")
def upload_internal_osz(
    request: Request,
    set_id: int,
    osz: UploadFile = File(...)
) -> Response:
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap set could not be found"
        )

    can_force_replace = permissions.has_permission(
        'beatmaps.moderation.resources',
        request.user.id
    )

    if beatmapset.status > 0 and not can_force_replace:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved and cannot be modified"
        )

    request.state.storage.upload_osz(
        beatmapset.id,
        osz.file.read(),
    )

    return Response(
        status_code=204,
        headers={"Location": f'/resources/osz/{beatmapset.id}'}
    )
