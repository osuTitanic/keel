
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import StreamingResponse
from datetime import timedelta
from io import BytesIO
from app import utils

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
        media_type="image/jpeg"
    )

@router.get("/mt/{filename}/small", response_class=StreamingResponse)
def get_internal_background_small(request: Request, filename: str):
    if file := request.state.storage.get_from_cache(f'mt:{filename}'):
        return StreamingResponse(
            BytesIO(file),
            media_type="image/jpeg"
        )

    if not (file := request.state.storage.get_background_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    # Resize image into 80x60
    file_iterator = utils.resize_image(file, 80, 60)

    # Save in cache
    request.state.storage.save_to_cache(
        name=f'mt:{filename}',
        content=file_iterator.getvalue(),
        expiry=timedelta(hours=6)
    )

    return StreamingResponse(
        file_iterator,
        media_type="image/jpeg"
    )
