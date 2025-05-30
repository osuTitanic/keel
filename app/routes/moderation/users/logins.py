
from fastapi import HTTPException, APIRouter, Request, Query
from app.common.database import logins, users
from app.models import LoginModel
from app.utils import requires
from typing import List

router = APIRouter()

@router.get("/logins", response_model=List[LoginModel])
@requires("users.moderation.logins")
def get_user_logins(
    request: Request,
    user_id: int,
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[LoginModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    recent_logins = logins.fetch_many(
        user.id,
        limit=limit,
        offset=offset,
        session=request.state.db
    )

    return [
        LoginModel.model_validate(login, from_attributes=True)
        for login in recent_logins
    ]
