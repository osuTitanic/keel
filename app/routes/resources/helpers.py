
from app.common.database.objects import DBBeatmap, DBBeatmapset
from app.common.database import beatmaps, beatmapsets
from app.common.helpers import permissions
from sqlalchemy.orm import Session
from fastapi import HTTPException

def validate_beatmap_for_upload(beatmap_id: int, user_id: int, db: Session) -> DBBeatmap:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    can_force_replace = permissions.has_permission(
        'beatmaps.moderation.resources',
        user_id
    )

    if beatmap.status > 0 and not can_force_replace:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved and cannot be modified"
        )

    return beatmap

def validate_beatmapset_for_upload(
    set_id: int,
    db: Session,
    user_id: int | None = None,
    require_unranked: bool = False,
) -> DBBeatmapset:
    if not (beatmapset := beatmapsets.fetch_one(set_id, db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap set could not be found"
        )

    if not require_unranked:
        return beatmapset

    can_force_replace = (
        user_id is not None and
        permissions.has_permission('beatmaps.moderation.resources', user_id)
    )

    if beatmapset.status > 0 and not can_force_replace:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved and cannot be modified"
        )

    return beatmapset
