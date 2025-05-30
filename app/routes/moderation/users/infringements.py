
from app.common.helpers import infringements as infringements_helper
from app.common.database import infringements, users
from app.models.moderation import *
from app.session import events
from app.utils import requires

from fastapi import HTTPException, APIRouter, Request, Query
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.get("/infringements", response_model=List[InfringementModel])
@requires("users.moderation.infringements")
def get_user_infringements(request: Request, user_id: int) -> List[InfringementModel]:
    return [
        InfringementModel.model_validate(infringement, from_attributes=True)
        for infringement in infringements.fetch_all(user_id, request.state.db)
    ]

@router.post("/infringements", response_model=InfringementModel)
@requires("users.moderation.infringements.create")
def create_user_infringement(
    request: Request,
    user_id: int,
    data: InfringementCreateRequest
) -> InfringementModel:
    actions = {
        InfringementAction.Restrict: handle_restrict,
        InfringementAction.Silence: handle_silence
    }

    if data.action not in actions:
        raise HTTPException(400, "Invalid action specified")

    return actions[data.action](request, user_id, data)

@router.patch("/infringements/{id}", response_model=InfringementModel)
@requires("users.moderation.infringements.update")
def update_user_infringement(
    request: Request,
    user_id: int,
    id: int,
    update: InfringementUpdateRequest
) -> InfringementModel:
    if not (record := infringements.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Infringement record not found")

    if record.user_id != user_id:
        raise HTTPException(400, "Infringement record does not belong to the specified user")

    if record.action == InfringementAction.Silence and update.is_permanent:
        raise HTTPException(400, "Silence records cannot be made permanent")

    success = infringements.update(
        record.id,
        {
            "duration": update.duration,
            "description": update.description,
            "is_permanent": update.is_permanent
        },
        request.state.db
    )

    if not success:
        raise HTTPException(500, "Failed to update infringement record")

    return InfringementModel.model_validate(
        infringements.fetch_one(id, request.state.db),
        from_attributes=True
    )

@router.delete("/infringements/{id}", response_model=InfringementModel)
@requires("users.moderation.infringements.delete")
def delete_user_infringement(
    request: Request,
    user_id: int,
    id: int,
    restore_scores: bool = Query(False)
) -> InfringementModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    if not (record := infringements.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Infringement record not found")

    if record.user_id != user.id:
        raise HTTPException(400, "Infringement record does not belong to the specified user")

    handlers = {
        0: lambda: infringements_helper.unrestrict_user(user, restore_scores, request.state.db),
        1: lambda: infringements_helper.unsilence_user(user, session=request.state.db)
    }

    if record.action not in handlers:
        raise HTTPException(400, "Invalid action for deletion")

    # Call the appropriate handler for the action
    handlers[record.action]()

    # Delete the infringement record
    infringements.delete_by_id(
        record.id,
        request.state.db
    )

    return InfringementModel.model_validate(
        record,
        from_attributes=True
    )

def handle_restrict(
    request: Request,
    user_id: int,
    data: InfringementCreateRequest
) -> InfringementModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    if user.restricted:
        raise HTTPException(400, "User is already restricted")

    record = infringements_helper.restrict_user(
        user,
        data.description,
        until=(
            datetime.now() + timedelta(seconds=data.duration)
            if not data.is_permanent else None
        ),
        session=request.state.db
    )

    if not record:
        raise HTTPException(500, "Failed to create infringement record")

    events.submit(
        "logout",
        user.id
    )

    return InfringementModel.model_validate(
        record,
        from_attributes=True
    )

def handle_silence(
    request: Request,
    user_id: int,
    data: InfringementCreateRequest
) -> InfringementModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    record = infringements_helper.silence_user(
        user,
        data.duration,
        data.description,
        session=request.state.db
    )

    if not record:
        raise HTTPException(500, "Failed to create infringement record")

    # Update user on bancho
    events.submit(
        "update_user_silence",
        user.id
    )

    return InfringementModel.model_validate(
        record,
        from_attributes=True
    )
