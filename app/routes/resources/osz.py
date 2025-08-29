
from fastapi import HTTPException, APIRouter, Request, UploadFile, Query, File
from fastapi.responses import StreamingResponse, Response
from app.common.database import beatmapsets
from app.common.helpers import permissions
from app.security import require_login
from typing import Generator, Tuple
from app.utils import requires
from zipfile import ZipFile
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

    if not (generator := request.state.storage.get_osz_iterable(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    if no_video:
        # Remove video files from the .osz file
        generator, size = remove_video_from_zip(generator)
        
    else:
        # Get regular osz size
        size = request.state.storage.get_osz_size(filename)

    return StreamingResponse(
        generator,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}.osz"',
            "Content-Length": f'{size}'
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

def remove_video_from_zip(osz: Generator) -> Tuple[Generator, int]:
    video_extensions = (
        ".wmv", ".flv", ".mp4",
        ".avi", ".m4v", ".mpg",
        ".mov", ".webm", ".mkv",
        ".ogv", ".mpeg", ".3gp"
    )

    with ZipFile(BytesIO(b"".join(osz)), 'r') as zip_file:
        files_to_keep = [
            item for item in zip_file.namelist()
            if not any(item.lower().endswith(ext) for ext in video_extensions)
        ]

        output = BytesIO()

        with ZipFile(output, 'w') as output_zip:
            for file in files_to_keep:
                output_zip.writestr(file, zip_file.read(file))

        output.seek(0)

        return (
            create_chunks_from_io(output),
            output.getbuffer().nbytes
        )

def create_chunks_from_io(output: BytesIO) -> Generator:
    while chunk := output.read(1024 * 64):
        yield chunk
