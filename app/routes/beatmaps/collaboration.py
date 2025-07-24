
from fastapi import HTTPException, APIRouter, Request, Body
from typing import List

from app.common.database import beatmaps, collaborations
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

@router.post("/{id}/collaborations/requests", response_model=CollaborationRequestModelWithoutBeatmap, dependencies=[require_login])
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

    if beatmap.beatmapset.creator_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
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
