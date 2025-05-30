
from fastapi import HTTPException, APIRouter, Request
from app.models import BadgeModel, BadgeUpdateRequest
from app.common.database import badges, users
from app.utils import requires
from typing import List

router = APIRouter()

@router.get("/badges", response_model=List[BadgeModel])
@requires("users.moderation.badges")
def get_user_badges(request: Request, user_id: int) -> List[BadgeModel]:
    return [
        BadgeModel.model_validate(badge, from_attributes=True)
        for badge in badges.fetch_all(user_id, request.state.db)
    ]

@router.post("/badges", response_model=BadgeModel)
@requires("users.moderation.badges.create")
def create_user_badge(
    request: Request,
    user_id: int,
    data: BadgeUpdateRequest
) -> BadgeModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    badge = badges.create(
        user.id,
        data.description,
        data.icon_url,
        data.badge_url,
        request.state.db
    )

    return BadgeModel.model_validate(
        badge,
        from_attributes=True
    )

@router.patch("/badges/{id}", response_model=BadgeModel)
@requires("users.moderation.badges.update")
def update_user_badge(
    request: Request,
    user_id: int,
    id: int,
    update: BadgeUpdateRequest
) -> BadgeModel:
    if not (badge := badges.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Badge not found")

    if badge.user_id != user_id:
        raise HTTPException(400, "Badge does not belong to the specified user")

    rows = badges.update(
        badge.id,
        {
            'badge_description': update.description,
            'badge_icon': update.icon_url,
            'badge_url': update.badge_url
        },
        request.state.db
    )

    if not rows:
        raise HTTPException(500, "Failed to update badge")

    return BadgeModel.model_validate(
        badge,
        from_attributes=True
    )

@router.delete("/badges/{id}", response_model=BadgeModel)
@requires("users.moderation.badges.delete")
def delete_user_badge(
    request: Request,
    user_id: int,
    id: int
) -> BadgeModel:
    if not (badge := badges.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Badge not found")

    if badge.user_id != user_id:
        raise HTTPException(400, "Badge does not belong to the specified user")

    success = badges.delete(
        id,
        request.state.db
    )

    if not success:
        raise HTTPException(500, "Failed to delete badge")

    return BadgeModel.model_validate(
        badge,
        from_attributes=True
    )
