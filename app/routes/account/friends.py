
from app.models import RelationshipResponse, UserModelCompact, ErrorResponse
from app.common.database import relationships, users
from app.security import require_login
from app.utils import requires

from fastapi import HTTPException, APIRouter, Request
from typing import List

router = APIRouter(
    responses={403: {'model': ErrorResponse, 'description': 'Authentication failure'}},
    dependencies=[require_login]
)

add_responses = {
    404: {'model': ErrorResponse, 'description': 'User not found'},
    400: {'model': ErrorResponse, 'description': 'Cannot add yourself as friend'}
}

remove_responses = {
    404: {'model': ErrorResponse, 'description': 'User not found'},
    400: {'model': ErrorResponse, 'description': 'You are not friends with this user'}
}

@router.get("/friends", response_model=List[UserModelCompact])
@requires("users.authenticated")
def friends(request: Request):
    """Get a list of friends for the authenticated user"""
    return [
        UserModelCompact.model_validate(friend.target, from_attributes=True)
        for friend in relationships.fetch_many_by_id(request.user.id, request.state.db)
        if friend.status == 0
    ]

@router.post("/friends", response_model=RelationshipResponse, responses=add_responses)
@requires("users.friends.create")
def add_friend(request: Request, id: int):
    """Add a user to the authenticated user's friends list"""
    if id == request.user.id:
        raise HTTPException(
            status_code=400,
            detail='You cannot add yourself as friend'
        )

    if not (target := users.fetch_by_id(id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )

    if not target.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
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

    target_friends = relationships.fetch_target_ids(
        target.id,
        request.state.db
    )

    if request.user.id in target_friends:
        return RelationshipResponse(status='mutual')

    return RelationshipResponse(status='friends')

@router.delete("/friends", response_model=RelationshipResponse, responses=remove_responses)
@requires("users.friends.delete")
def remove_friend(request: Request, id: int):
    """Remove a user from the authenticated user's friends list"""
    if not (target := users.fetch_by_id(id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )

    current_friends = relationships.fetch_target_ids(
        request.user.id,
        request.state.db
    )

    if target.id not in current_friends:
        raise HTTPException(
            status_code=400,
            detail='You are not friends with this user'
        )
    
    relationships.delete(
        request.user.id,
        target.id,
        status=0,
        session=request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} removed {target.name} from their friends list.'
    )

    target_friends = relationships.fetch_target_ids(
        target.id,
        request.state.db
    )

    if request.user.id in target_friends:
        return RelationshipResponse(status='mutual')

    return RelationshipResponse(status='friends')
