
from fastapi import HTTPException, APIRouter, Request, Body
from typing import List

from app.common.database import beatmaps, collaborations, notifications
from app.common.constants import NotificationType
from app.models.collaboration import *
from app.security import require_login
from app.utils import requires

router = APIRouter()

@router.get("/{id}/collaborations", response_model=List[CollaborationModelWithoutBeatmap])
def get_collaborations(request: Request, id: int) -> List[CollaborationModelWithoutBeatmap]:
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    return [
        CollaborationModelWithoutBeatmap.model_validate(collaboration, from_attributes=True)
        for collaboration in collaborations.fetch_by_beatmap(id, request.state.db)
    ]

@router.patch("/{beatmap_id}/collaborations/{user_id}", response_model=CollaborationModelWithoutBeatmap, dependencies=[require_login])
@requires("users.authenticated")
def update_collaboration(
    request: Request,
    beatmap_id: int,
    user_id: int,
    data: CollaborationUpdateRequest = Body(...)
) -> CollaborationModelWithoutBeatmap:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )
        
    if beatmap.status > 0:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved"
        )

    if not (collaboration := collaborations.fetch_one(beatmap_id, user_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested collaboration request could not be found"
        )

    if collaboration.beatmap_id != beatmap_id:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    collaborations.update(
        beatmap_id, user_id,
        {
            "allow_resource_updates": data.allow_resource_updates,
            "is_beatmap_author": data.is_beatmap_author
        },
        session=request.state.db
    )
    request.state.db.refresh(collaboration)

    return CollaborationModelWithoutBeatmap.model_validate(
        collaboration,
        from_attributes=True
    )

@router.get("/{id}/collaborations/requests", response_model=List[CollaborationRequestModelWithoutBeatmap], dependencies=[require_login])
@requires("users.authenticated")
def get_collaboration_requests(request: Request, id: int) -> List[CollaborationRequestModelWithoutBeatmap]:
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    return [
        CollaborationRequestModelWithoutBeatmap.model_validate(collaboration, from_attributes=True)
        for collaboration in collaborations.fetch_requests_outgoing(id, request.state.db)
    ]

@router.post("/{beatmap_id}/collaborations/requests", response_model=CollaborationRequestModelWithoutBeatmap, dependencies=[require_login])
@requires("users.authenticated")
def create_collaboration_request(
    request: Request,
    beatmap_id: int,
    data: CollaborationCreateRequest = Body(...)
) -> CollaborationRequestModelWithoutBeatmap:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )
        
    if beatmap.status > 0:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved"
        )

    if beatmap.beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )
        
    if request.user.id == data.user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot send an invite to yourself"
        )

    is_blacklisted = collaborations.is_blacklisted(
        data.user_id,
        request.user.id,
        request.state.db
    )

    if is_blacklisted:
        raise HTTPException(
            status_code=403,
            detail="This user blacklisted you from collaboration invites"
        )

    exists = collaborations.exists(
        user_id=data.user_id,
        beatmap_id=beatmap_id,
        session=request.state.db
    )

    if exists:
        raise HTTPException(
            status_code=400,
            detail="This user is already collaborating on this beatmap"
        )

    request_count = collaborations.fetch_request_count(
        beatmap_id,
        request.state.db
    )

    if request_count >= 6:
        raise HTTPException(
            status_code=400,
            detail="You cannot send more than 6 collaboration requests for a single beatmap"
        )

    collaboration = collaborations.create_request(
        user_id=request.user.id,
        target_id=data.user_id,
        beatmap_id=beatmap_id,
        session=request.state.db
    )

    return CollaborationRequestModelWithoutBeatmap.model_validate(
        collaboration,
        from_attributes=True
    )

@router.delete("/{beatmap_id}/collaborations/{user_id}", dependencies=[require_login])
@requires("users.authenticated")
def delete_collaboration(
    request: Request,
    beatmap_id: int,
    user_id: int
) -> dict:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status > 0:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved"
        )

    if not (collaboration := collaborations.fetch_one(beatmap_id, user_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested collaboration could not be found"
        )

    if collaboration.beatmap_id != beatmap_id:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    success = collaborations.delete(
        beatmap_id, user_id,
        request.state.db
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the collaboration"
        )

    return {}

@router.delete("/{beatmap_id}/collaborations/requests/{id}", dependencies=[require_login])
@requires("users.authenticated")
def delete_collaboration_request(
    request: Request,
    beatmap_id: int,
    id: int
) -> dict:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )
        
    if beatmap.status > 0:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved"
        )
        
    if not (collaboration := collaborations.fetch_request(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested invitation could not be found"
        )

    if collaboration.beatmap_id != beatmap_id:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    # Only the beatmap creator or the target user can delete the request
    is_authorized = (
        beatmap.beatmapset.creator_id == request.user.id or
        collaboration.target_id == request.user.id
    )

    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    success = collaborations.delete_request(id, request.state.db)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the collaboration request"
        )

    # Send notification to creator
    if beatmap.beatmapset.creator_id != request.user.id:
        notifications.create(
            beatmap.beatmapset.creator_id,
            NotificationType.Other,
            header="Collaboration Invite Declined",
            content=(
                f"{request.user.name} has declined your invite to "
                f'collaborate on "{beatmap.full_name}".'
            ),
            link=f"/b/{beatmap.id}",
            session=request.state.db
        )

    return {}

@router.post("/{beatmap_id}/collaborations/requests/{id}/accept", dependencies=[require_login])
@requires("users.authenticated")
def accept_collaboration_request(
    request: Request,
    beatmap_id: int,
    id: int
) -> CollaborationModel:
    if not (pending := collaborations.fetch_request(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested collaboration request could not be found"
        )

    if pending.beatmap_id != beatmap_id:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )
        
    if not pending.beatmap:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if pending.beatmap.status > 0:
        raise HTTPException(
            status_code=400,
            detail="This beatmap is already approved"
        )

    if pending.target_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    collaboration = collaborations.create(
        pending.beatmap_id,
        pending.target_id,
        is_beatmap_author=False,
        allow_resource_updates=pending.allow_resource_updates,
        session=request.state.db
    )

    # Remove collaboration request
    collaborations.delete_request(id, request.state.db)

    # Send notification to creator
    if pending.beatmap.beatmapset.creator_id != request.user.id:
        notifications.create(
            pending.beatmap.beatmapset.creator_id,
            NotificationType.Other,
            header="Collaboration Invite Accepted",
            content=(
                f"{request.user.name} has accepted your invite to "
                f'collaborate on "{pending.beatmap.full_name}".'
            ),
            link=f"/b/{pending.beatmap.id}",
            session=request.state.db
        )

    return CollaborationModel.model_validate(
        collaboration,
        from_attributes=True
    )
