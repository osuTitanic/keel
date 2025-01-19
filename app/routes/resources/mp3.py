
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import StreamingResponse
from app.utils import file_iterator

router = APIRouter()

@router.get('/mp3/{filename}')
def get_internal_mp3(request: Request, filename: str):
    if not (file := request.state.storage.get_mp3_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        file_iterator(file),
        media_type="audio/mpeg"
    )
