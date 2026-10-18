
from .helpers import validate_beatmap_for_upload

from fastapi import HTTPException, APIRouter, Request, UploadFile, File, Query
from fastapi.responses import PlainTextResponse, Response
from datetime import datetime
from hashlib import md5

from app.common.database.repositories import beatmaps
from app.security import require_login
from app.utils import requires

router = APIRouter()

@router.get("/osu/{filename}", response_class=PlainTextResponse)
def get_internal_beatmap(request: Request, filename: str):
    if not (file := request.state.storage.get_beatmap(filename)):
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
    osu: UploadFile = File(...),
    update_filename: bool = Query(False)
) -> Response:
    beatmap = validate_beatmap_for_upload(beatmap_id, request.user.id, request.state.db)
    beatmap_data = osu.file.read()

    updates = {
        "md5": md5(beatmap_data).hexdigest(),
        "last_update": datetime.now()
    }

    if update_filename:
        if not osu.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename must be provided when updating the filename"
            )

        if not osu.filename.endswith(".osu"):
            raise HTTPException(
                status_code=400,
                detail="Filename must end with .osu"
            )

        updates["filename"] = osu.filename

    request.state.storage.upload_beatmap_file(
        beatmap.id,
        beatmap_data
    )
    beatmaps.update(
        beatmap.id,
        updates,
        request.state.db
    )

    return Response(
        status_code=204,
        headers={"Location": f'/resources/osu/{beatmap.id}'}
    )
