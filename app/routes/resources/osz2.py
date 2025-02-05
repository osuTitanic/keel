
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import StreamingResponse
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={403: {'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get("/osz2/{filename}")
@requires("authenticated")
def get_internal_osz2(request: Request, filename: str):
    if not (file := request.state.storage.get_osz2_iterable(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return StreamingResponse(
        file,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.osz2"'}
    )
