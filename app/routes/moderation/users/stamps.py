
from fastapi import HTTPException, APIRouter, Request
from app.models import StampModel, StampUpdateRequest
from app.common.database import stamps, users
from app.utils import requires
from typing import List

router = APIRouter()

@router.get("/stamps", response_model=List[StampModel])
@requires("users.moderation.stamps")
def get_user_stamps(request: Request, user_id: int) -> List[StampModel]:
    return [
        StampModel.model_validate(stamp, from_attributes=True)
        for stamp in stamps.fetch_all(user_id, request.state.db)
    ]

@router.post("/stamps", response_model=StampModel)
@requires("users.moderation.stamps.create")
def create_user_stamp(
    request: Request,
    user_id: int,
    data: StampUpdateRequest
) -> StampModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    stamp = stamps.create(
        user.id,
        data.description,
        data.icon_url,
        data.stamp_url,
        request.state.db
    )

    return StampModel.model_validate(
        stamp,
        from_attributes=True
    )

@router.patch("/stamps/{id}", response_model=StampModel)
@requires("users.moderation.stamps.update")
def update_user_stamp(
    request: Request,
    user_id: int,
    id: int,
    update: StampUpdateRequest
) -> StampModel:
    if not (stamp := stamps.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Stamp not found")

    if stamp.user_id != user_id:
        raise HTTPException(400, "Stamp does not belong to the specified user")

    rows = stamps.update(
        stamp.id,
        {
            'description': update.description,
            'icon': update.icon_url,
            'url': update.stamp_url
        },
        request.state.db
    )

    if not rows:
        raise HTTPException(500, "Failed to update stamp")

    return StampModel.model_validate(
        stamp,
        from_attributes=True
    )

@router.delete("/stamps/{id}", response_model=StampModel)
@requires("users.moderation.stamps.delete")
def delete_user_stamp(
    request: Request,
    user_id: int,
    id: int
) -> StampModel:
    if not (stamp := stamps.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Stamp not found")

    if stamp.user_id != user_id:
        raise HTTPException(400, "Stamp does not belong to the specified user")

    success = stamps.delete(
        id,
        request.state.db
    )

    if not success:
        raise HTTPException(500, "Failed to delete stamp")

    return StampModel.model_validate(
        stamp,
        from_attributes=True
    )
