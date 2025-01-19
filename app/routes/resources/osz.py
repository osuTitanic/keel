
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import StreamingResponse
from app.utils import file_iterator

router = APIRouter()

@router.get('/osz/{filename}')
def get_internal_osz(request: Request, filename: str):
    if not (file := request.state.storage.get_osz_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        file_iterator(file, chunk_size=1024*1024),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.osz"'}
    )
