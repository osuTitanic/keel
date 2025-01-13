
from app.models import UserModelCompact, ErrorResponse
from starlette.authentication import requires
from app.common.database import relationships
from app.security import require_login
from fastapi import APIRouter, Request
from typing import List

router = APIRouter(
    responses={403: {'model': ErrorResponse, 'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get('/friends', response_model=List[UserModelCompact])
@requires('authenticated')
def friends(request: Request):
    return [
        UserModelCompact.model_validate(friend.target, from_attributes=True)
        for friend in relationships.fetch_many_by_id(request.user.id, request.state.db)
        if friend.status == 0
    ]
