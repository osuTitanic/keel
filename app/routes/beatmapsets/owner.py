

from fastapi import HTTPException, APIRouter, Request, Body
from app.common.database import beatmapsets, users
from app.security import require_login
from app.utils import requires
from app.models import *

router = APIRouter(
    dependencies=[require_login],
    responses={
        404: {'model': ErrorResponse, 'description': 'Beatmapset or topic not found'},
        401: {'model': ErrorResponse, 'description': 'Authentication failure'},
        400: {'model': ErrorResponse, 'description': 'Invalid request'}
    }
)

@router.patch("/{set_id}/owner", response_model=BeatmapsetModel)
@requires("beatmaps.moderation.owner")
def change_beatmap_owner(
    request: Request,
    set_id: int,
    update: BeatmapsetOwnerUpdate = Body(...)
) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(404, 'The requested beatmapset could not be found')
    
    if not (new_owner := users.fetch_by_id(update.user_id, session=request.state.db)):
        raise HTTPException(404, 'The specified user could not be found')

    if beatmapset.creator_id == new_owner.id:
        raise HTTPException(400, 'This user is already the owner of this beatmapset')

    beatmapsets.update(
        beatmapset.id,
        {'creator_id': new_owner.id},
        request.state.db
    )
    request.state.db.refresh(beatmapset)

    return BeatmapsetModel.model_validate(
        beatmapset,
        from_attributes=True
    )
