
from fastapi import HTTPException, APIRouter, Request
from app.common.database.repositories import users
from app.models import UserModel

router = APIRouter()

@router.get("/{user_id}")
def get_user_profile(request: Request, user_id: int) -> UserModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail="The requested user was not found"
        )

    return UserModel.model_validate(user, from_attributes=True)
