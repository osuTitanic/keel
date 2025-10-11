
from fastapi import HTTPException, APIRouter, Request
from app.common.database import users
from app.utils import requires
from datetime import datetime

router = APIRouter()

@router.delete("/avatar")
@requires("users.moderation.avatar")
def remove_user_avatar(
    request: Request,
    user_id: int
) -> dict:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    # Remove avatar from storage
    request.state.storage.remove_avatar(user.id)

    # Set last avatar update time
    users.update(
        user.id,
        {"avatar_last_update": datetime.now()},
        request.state.db
    )
    return {}
