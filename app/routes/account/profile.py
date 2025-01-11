
from starlette.authentication import requires
from fastapi import APIRouter, Request
from app.models import UserModel

router = APIRouter()

@router.get('/profile', response_model=UserModel)
@requires('authenticated')
def user_profile(request: Request) -> UserModel:
    return UserModel.model_validate(
        request.user,
        from_attributes=True
    )
