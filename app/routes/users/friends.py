
from fastapi import HTTPException, Request, APIRouter
from app.common.database import users, relationships
from app.models import UserModelCompact
from typing import List

router = APIRouter()

@router.get('/{user_id}/friends', response_model=List[UserModelCompact])
def get_friends(request: Request, user_id: int) -> List[UserModelCompact]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    return [
        UserModelCompact.model_validate(friend.target, from_attributes=True)
        for friend in relationships.fetch_many_by_id(user.id, request.state.db)
        if friend.status == 0
    ]
