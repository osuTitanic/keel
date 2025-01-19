
from fastapi import HTTPException, APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from app.utils import file_iterator
from zipfile import ZipFile
from io import BytesIO

router = APIRouter()

@router.get('/osz/{filename}')
def get_internal_osz(
    request: Request,
    filename: str,
    no_video: bool = Query(False)
) -> StreamingResponse:
    if not (file := request.state.storage.get_osz_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    if no_video:
        # Remove video files from the .osz file
        file = remove_video_from_zip(file)

    return StreamingResponse(
        file_iterator(file, chunk_size=1024*1024),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.osz"'}
    )

def remove_video_from_zip(osz: bytes) -> bytes:
    video_extensions = [
        ".wmv", ".flv", ".mp4", ".avi", ".m4v"
    ]

    with ZipFile(BytesIO(osz), 'r') as zip_file:
        files_to_keep = [
            item for item in zip_file.namelist()
            if not any(item.lower().endswith(ext) for ext in video_extensions)
        ]

        output = BytesIO()

        with ZipFile(output, 'w') as output_zip:
            for file in files_to_keep:
                output_zip.writestr(file, zip_file.read(file))

        return output.getvalue()
