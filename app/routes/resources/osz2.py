
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import StreamingResponse
from app.utils import requires, is_empty_generator
from app.security import require_login

router = APIRouter(
    responses={403: {'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get("/osz2/{filename}", response_class=StreamingResponse)
@requires("beatmaps.download")
def get_internal_osz2(request: Request, filename: str):
    if not request.state.storage.file_exists(filename, 'osz2'):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    if not (generator := request.state.storage.get_osz2_iterable(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        generator,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.osz2"'}
    )
