
from app.common.database import achievements, users
from app.models import AchievementModel

from fastapi import HTTPException, Request, APIRouter
from typing import List

router = APIRouter()

@router.get("/{user_id}/achievements", response_model=List[AchievementModel])
def get_user_achievements(request: Request, user_id: int) -> List[AchievementModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )

    return [
        AchievementModel.model_validate(achievement, from_attributes=True)
        for achievement in achievements.fetch_many(user.id, request.state.db)
    ]
