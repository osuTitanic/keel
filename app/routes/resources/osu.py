
from fastapi import HTTPException, APIRouter, Request, UploadFile, File
from fastapi.responses import PlainTextResponse, Response
from app.common.helpers import permissions
from app.common.database import beatmaps
from app.security import require_login
from app.utils import requires
from datetime import datetime
from hashlib import md5

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
        media_type="text/plain"
    )

@router.put("/osu/{beatmap_id}", dependencies=[require_login])
@requires("beatmaps.resources.osu.upload")
def upload_internal_beatmap(
    request: Request,
    beatmap_id: int,
    osu: UploadFile = File(...)
) -> Response:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap set could not be found"
        )

    can_force_replace = permissions.has_permission(
        'beatmaps.moderation.resources',
        request.user.id
    )

    if beatmap.status > 0 and not can_force_replace:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved and cannot be modified"
        )

    beatmap_data = osu.file.read()
    beatmap_hash = md5(beatmap_data).hexdigest()

    request.state.storage.upload_beatmap_file(
        beatmap.id,
        beatmap_data,
    )

    beatmaps.update(
        beatmap.id,
        {
            "md5": beatmap_hash,
            "last_update": datetime.now()
        },
        request.state.db
    )

    return Response(
        status_code=204,
        headers={"Location": f'/resources/osu/{beatmap.id}'}
    )
