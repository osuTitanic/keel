
from .helpers import validate_beatmap_for_upload

from fastapi import HTTPException, APIRouter, Request, UploadFile, File
from fastapi.responses import PlainTextResponse, Response
from datetime import datetime
from hashlib import md5

from app.common.database.repositories import beatmaps
from app.security import require_login
from app.utils import requires

router = APIRouter()

@router.get("/osu/{filename}", response_class=PlainTextResponse)
def get_internal_beatmap(request: Request, filename: str):
    if not (file := request.state.storage.get_beatmap_internal(filename)):
        raise HTTPException(
            status_code=404,
            detail="The requested resource could not be found"
        )

    return PlainTextResponse(
        file,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}.osu"',
            "Content-Length": f'{len(file)}'
        }
    )

@router.put("/osu/{beatmap_id}", dependencies=[require_login])
@requires("beatmaps.resources.osu.upload")
def upload_internal_beatmap(
    request: Request,
    beatmap_id: int,
    osu: UploadFile = File(...)
) -> Response:
    beatmap = validate_beatmap_for_upload(beatmap_id, request.user.id, request.state.db)
    beatmap_data = osu.file.read()

    request.state.storage.upload_beatmap_file(
        beatmap.id,
        beatmap_data
    )
    beatmaps.update(
        beatmap.id,
        {
            "md5": md5(beatmap_data).hexdigest(),
            "last_update": datetime.now()
        },
        request.state.db
    )

    return Response(
        status_code=204,
        headers={"Location": f'/resources/osu/{beatmap.id}'}
    )
