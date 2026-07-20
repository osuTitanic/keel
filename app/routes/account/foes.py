
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

block_responses = {
    404: {'model': ErrorResponse, 'description': 'User not found'},
    400: {'model': ErrorResponse, 'description': 'Cannot block yourself'}
}

unblock_responses = {
    404: {'model': ErrorResponse, 'description': 'User not found'},
    400: {'model': ErrorResponse, 'description': 'You have not blocked this user'}
}

@router.get("/foes", response_model=List[UserModelCompact])
@requires("users.friends.view")
def foes(request: Request):
    """Get a list of users blocked by the authenticated user"""
    return [
        UserModelCompact.model_validate(user, from_attributes=True)
        for user in relationships.fetch_users(
            request.user.id,
            status=1,
            session=request.state.db
        )
    ]

@router.post("/foes", response_model=RelationshipResponse, responses=block_responses)
@requires("users.friends.create")
def block_user(request: Request, id: int):
    """Block a user and remove them from the authenticated user's friends list"""
    if id == request.user.id:
        raise HTTPException(
            status_code=400,
            detail='You cannot block yourself'
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
    
    is_friend = relationships.is_friend(
        request.user.id,
        target.id,
        session=request.state.db
    )

    # Remove friend status if the user is a friend before blocking them
    if is_friend:
        relationships.delete(
            request.user.id,
            target.id,
            status=0,
            session=request.state.db
        )

    is_blocked = relationships.is_blocked(
        request.user.id,
        target.id,
        session=request.state.db
    )

    if not is_blocked:
        relationships.create(
            request.user.id,
            target.id,
            status=1,
            session=request.state.db
        )

    request.state.logger.info(
        f'{request.user.name} blocked {target.name}.'
    )
    return RelationshipResponse(status='blocked')

@router.delete("/foes", response_model=RelationshipResponse, responses=unblock_responses)
@requires("users.friends.delete")
def unblock_user(request: Request, id: int):
    """Unblock a user"""
    if not (target := users.fetch_by_id(id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )
    
    is_blocked = relationships.is_blocked(
        request.user.id,
        target.id,
        session=request.state.db
    )

    if not is_blocked:
        raise HTTPException(
            status_code=400,
            detail='You have not blocked this user'
        )

    relationships.delete(
        request.user.id,
        target.id,
        status=1,
        session=request.state.db
    )

    request.state.logger.info(
        f'{request.user.name} unblocked {target.name}.'
    )
    return RelationshipResponse(status='unblocked')
