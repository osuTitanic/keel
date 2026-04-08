
from fastapi import HTTPException, APIRouter, Request, Body
from app.common.database import beatmapsets, users, topics
from app.common.helpers import permissions
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

@router.patch('/{beatmapset_id}/link', response_model=BeatmapsetModel)
@requires('beatmaps.link')
def link_beatmapset_to_topic(
    request: Request,
    beatmapset_id: int,
    link_request: BeatmapsetLinkRequest = Body(...)
) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(beatmapset_id, request.state.db)):
        raise HTTPException(404, 'The requested beatmapset could not be found')

    if not (topic := topics.fetch_one(link_request.topic_id, request.state.db)):
        raise HTTPException(404, 'The specified topic could not be found')

    can_force_update = permissions.has_permission(
        'beatmaps.moderation.force_link',
        request.user.id
    )

    if beatmapset.server != 0 and not can_force_update:
        raise HTTPException(400, "This beatmapset was uploaded to titanic and can't be manually linked to a topic.")

    # Check if topic was already linked to another set
    existing_set = beatmapsets.fetch_by_topic(
        link_request.topic_id,
        request.state.db
    )

    if existing_set and existing_set.id != beatmapset.id:
        # Unlink the existing set
        beatmapsets.update(
            existing_set.id,
            {'topic_id': None},
            request.state.db
        )

    beatmapsets.update(
        beatmapset.id,
        {'topic_id': topic.id},
        request.state.db
    )
    request.state.db.refresh(beatmapset)

    return BeatmapsetModel.model_validate(
        beatmapset,
        from_attributes=True
    )

@router.delete('/{beatmapset_id}/link', response_model=BeatmapsetModel)
@requires('beatmaps.link')
def unlink_beatmapset_from_topic(request: Request, beatmapset_id: int) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(beatmapset_id, request.state.db)):
        raise HTTPException(404, 'The requested beatmapset could not be found')

    if beatmapset.server != 0:
        raise HTTPException(400, "This beatmapset was uploaded to titanic and can't be manually unlinked from a topic.")

    beatmapsets.update(
        beatmapset.id,
        {'topic_id': None},
        request.state.db
    )
    request.state.db.refresh(beatmapset)

    return BeatmapsetModel.model_validate(
        beatmapset,
        from_attributes=True
    )
