
from app.common.database.objects import DBUser
from app.common.database import users
from app.models import UserModel

from fastapi import HTTPException, APIRouter, Request
from sqlalchemy.orm import Session

router = APIRouter()

@router.get('/lookup/{input}', response_model=UserModel)
def user_lookup(request: Request, input: str) -> UserModel:
    if not (user := resolve_user_profile(input, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail='The requested user was not found'
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user was not found'
        )

    return UserModel.model_validate(user, from_attributes=True)

def resolve_user_profile(input: str, session: Session) -> DBUser | None:
    if input.isdigit():
        return users.fetch_by_id(
            int(input),
            session=session
        )

    return users.fetch_by_name_extended(
        input,
        session
    )
