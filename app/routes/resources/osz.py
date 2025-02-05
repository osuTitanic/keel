
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from app.security import require_login
from app.utils import requires
from zipfile import ZipFile
from io import BytesIO


router = APIRouter(
    responses={403: {'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get("/osz/{filename}")
@requires("authenticated")
def get_internal_osz(
    request: Request,
    filename: str,
    no_video: bool = Query(False)
) -> StreamingResponse:
    if not (file := request.state.storage.get_osz_iterable(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    if no_video:
        # Remove video files from the .osz file
        file = remove_video_from_zip(file)

    return StreamingResponse(
        file,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.osz"'}
    )

def remove_video_from_zip(osz: BytesIO) -> BytesIO:
    video_extensions = [
        ".wmv", ".flv", ".mp4", ".avi", ".m4v"
    ]

    with ZipFile(osz, 'r') as zip_file:
        files_to_keep = [
            item for item in zip_file.namelist()
            if not any(item.lower().endswith(ext) for ext in video_extensions)
        ]

        output = BytesIO()

        with ZipFile(output, 'w') as output_zip:
            for file in files_to_keep:
                output_zip.writestr(file, zip_file.read(file))

        output.seek(0)
        return output
