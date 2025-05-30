
from fastapi import HTTPException, APIRouter, Request
from app.models import UserMetadataModel, UserMetadataUpdateRequest
from app.common.database import logins, users
from app.common.cache import leaderboards
from app.utils import requires
from typing import List

router = APIRouter()

@router.get("/profile", response_model=UserMetadataModel)
@requires("users.moderation.profile")
def get_user_profile(
    request: Request,
    user_id: int
) -> UserMetadataModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    return UserMetadataModel.model_validate(
        user,
        from_attributes=True
    )

@router.patch("/profile", response_model=UserMetadataModel)
@requires("users.moderation.profile.update")
def update_user_profile(
    request: Request,
    user_id: int,
    update: UserMetadataUpdateRequest
) -> UserMetadataModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    if update.country.lower() != user.country.lower():
        # Remove from old country leaderboard
        leaderboards.remove_country(user.id, user.country)

        for stats in user.stats:
            # Re-add to leaderboard with new country
            leaderboards.update(stats, update.country)

    success = users.update(
        user.id,
        {
            "country": update.country,
            "email": update.email,
            "is_bot": update.is_bot,
            "activated": update.activated,
            "discord_id": update.discord_id,
            "userpage": update.userpage,
            "signature": update.signature,
            "title": update.title,
            "banner": update.banner,
            "website": update.website,
            "discord": update.discord,
            "twitter": update.twitter,
            "location": update.location,
            "interests": update.interests
        },
        request.state.db
    )

    if not success:
        raise HTTPException(500, "Failed to update user profile")

    # Refresh user object
    request.state.db.refresh(user)

    return UserMetadataModel.model_validate(
        user,
        from_attributes=True
    )
