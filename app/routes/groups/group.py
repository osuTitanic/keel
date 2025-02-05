
from app.models import UserModelCompact, GroupModel, ErrorResponse
from app.common.database import groups

from fastapi import HTTPException, APIRouter, Request
from typing import List

router = APIRouter()
responses = {404: {"description": "The requested group could not be found", "model": ErrorResponse}}

@router.get('/', response_model=List[GroupModel])
def get_groups(request: Request) -> List[GroupModel]:
    return [
        GroupModel.model_validate(group, from_attributes=True)
        for group in groups.fetch_all(session=request.state.db)
    ]

@router.get('/{id}', response_model=GroupModel, responses=responses)
def get_group(request: Request, id: int) -> GroupModel:
    if not (group := groups.fetch_one(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested group could not be found"
        )

    if group.hidden:
        raise HTTPException(
            status_code=404,
            detail="The requested group could not be found"
        )

    return GroupModel.model_validate(group, from_attributes=True)

@router.get('/{id}/users', response_model=List[UserModelCompact], responses=responses)
def get_group_users(request: Request, id: int) -> List[UserModelCompact]:
    if not (group := groups.fetch_one(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested group could not be found"
        )

    if group.hidden:
        raise HTTPException(
            status_code=404,
            detail="The requested group could not be found"
        )

    users = groups.fetch_group_users(
        group.id,
        request.state.db
    )

    return [
        UserModelCompact.model_validate(user, from_attributes=True)
        for user in users
    ]
