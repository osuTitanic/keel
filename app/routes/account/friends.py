
from app.models import RelationshipResponseModel, UserModelCompact, ErrorResponse
from app.common.database import relationships, users
from app.security import require_login

from fastapi import HTTPException, APIRouter, Request
from starlette.authentication import requires
from typing import List

router = APIRouter(
    responses={403: {'model': ErrorResponse, 'description': 'Authentication failure'}},
    dependencies=[require_login]
)

add_responses = {
    404: {'model': ErrorResponse, 'description': 'User not found'},
    400: {'model': ErrorResponse, 'description': 'Cannot add yourself as friend'}
}

@router.get('/friends', response_model=List[UserModelCompact])
@requires('authenticated')
def friends(request: Request):
    return [
        UserModelCompact.model_validate(friend.target, from_attributes=True)
        for friend in relationships.fetch_many_by_id(request.user.id, request.state.db)
        if friend.status == 0
    ]

@router.post('/friends', response_model=RelationshipResponseModel, responses=add_responses)
@requires('authenticated')
def add_friend(request: Request, target_id: int):
    if target_id == request.user.id:
        raise HTTPException(
            status_code=400,
            detail='Cannot add yourself as friend'
        )

    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail='User not found'
        )

    if not target.activated:
        raise HTTPException(
            status_code=404,
            detail='User not found'
        )
    
    current_friends = relationships.fetch_target_ids(
        request.user.id,
        request.state.db
    )

    if target.id not in current_friends:
        # Create relationship
        relationships.create(
            request.user.id,
            target.id,
            status=0,
            session=request.state.db
        )

    request.state.logger.info(
        f'{request.user.name} added {target.name} to their friends list.'
    )

    # Check for mutual
    target_friends = relationships.fetch_target_ids(
        target.id,
        request.state.db
    )

    if request.user.id in target_friends:
        return RelationshipResponseModel(status='mutual')

    return RelationshipResponseModel(status='friends')
