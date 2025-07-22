
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import RedirectResponse
from typing import List

from app.models import IrcTokenResponse
from app.utils import requires

router = APIRouter()

@router.get("/irc/token", response_model=IrcTokenResponse)
@requires("users.authenticated")
def irc_token(request: Request) -> IrcTokenResponse:
    if request.user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="For security reasons, admins cannot view their IRC token"
        )
        
    return IrcTokenResponse(
        username=request.user.name.replace(' ', '_'),
        token=request.user.irc_token
    )
