
from app.models import NominationModelWithBeatmapset
from app.common.database import users, nominations

from fastapi import HTTPException, APIRouter, Request
from typing import List

router = APIRouter()

@router.get("/{user_id}/nominations", response_model=List[NominationModelWithBeatmapset])
def get_user_nominations(request: Request, user_id: int) -> List[NominationModelWithBeatmapset]:
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

    user_nominations = nominations.fetch_by_user(
        user.id,
        request.state.db
    )

    return [
        NominationModelWithBeatmapset.model_validate(nomination, from_attributes=True)
        for nomination in user_nominations
    ]
