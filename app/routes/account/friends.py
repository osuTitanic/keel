
from fastapi import APIRouter, Request, Depends
from starlette.authentication import requires
from app.common.database import relationships
from app.models import UserModelCompact
from sqlalchemy.orm import Session
from typing import List
import app

router = APIRouter()

@router.get('/friends', response_model=List[UserModelCompact])
@requires('authenticated')
def friends(request: Request):
    return [
        UserModelCompact.model_validate(friend.target, from_attributes=True)
        for friend in relationships.fetch_many_by_id(request.user.id, request.state.db)
    ]
