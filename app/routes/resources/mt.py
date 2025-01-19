
from app.utils import file_iterator, resize_image
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import StreamingResponse
from datetime import timedelta

router = APIRouter()

@router.get('/mt/{filename}')
def get_internal_background_large(request: Request, filename: str):
    if not (file := request.state.storage.get_background_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        file_iterator(file),
        media_type="image/jpeg"
    )

@router.get('/mt/{filename}/small')
def get_internal_background_small(request: Request, filename: str):
    if file := request.state.storage.get_from_cache(f'mt:{filename}'):
        return StreamingResponse(
            file_iterator(file),
            media_type="image/jpeg"
        )

    if not (file := request.state.storage.get_background_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    # Resize image into 80x60
    file = resize_image(file, 80, 60)

    # Save in cache
    request.state.storage.save_to_cache(
        name=f'mt:{filename}',
        content=file,
        expiry=timedelta(hours=6)
    )

    return StreamingResponse(
        file_iterator(file),
        media_type="image/jpeg"
    )
