
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from app.utils import requires, is_empty_generator
from app.security import require_login
from typing import Generator
from zipfile import ZipFile
from io import BytesIO


router = APIRouter(
    responses={403: {'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get("/osz/{filename}", response_class=StreamingResponse)
@requires("authenticated")
def get_internal_osz(
    request: Request,
    filename: str,
    no_video: bool = Query(False)
) -> StreamingResponse:
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
        generator = remove_video_from_zip(generator)

    return StreamingResponse(
        generator,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.osz"'}
    )

def remove_video_from_zip(osz: Generator) -> Generator:
    video_extensions = (".wmv", ".flv", ".mp4", ".avi", ".m4v")
    osz_io = BytesIO(b"".join(osz))

    with ZipFile(osz_io, 'r') as zip_file:
        files_to_keep = [
            item for item in zip_file.namelist()
            if not any(item.lower().endswith(ext) for ext in video_extensions)
        ]

        output = BytesIO()

        with ZipFile(output, 'w') as output_zip:
            for file in files_to_keep:
                output_zip.writestr(file, zip_file.read(file))

        output.seek(0)

        while chunk := output.read(1024 * 64):
            yield chunk
