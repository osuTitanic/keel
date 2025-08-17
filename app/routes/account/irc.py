
from fastapi import HTTPException, APIRouter, Request
from app.common.database.repositories import users
from app.utils import requires, random_string
from app.models import IrcTokenResponse

router = APIRouter()

@router.get("/irc/token", response_model=IrcTokenResponse)
@requires("users.authenticated")
def irc_token(request: Request) -> IrcTokenResponse:        
    return IrcTokenResponse(
        username=request.user.name.replace(' ', '_'),
        token=request.user.irc_token
    )

@router.post("/irc/token", response_model=IrcTokenResponse)
@requires("users.authenticated")
def regenerate_irc_token(request: Request) -> IrcTokenResponse:
    request.user.irc_token = random_string(length=10)

    users.update(
        request.user.id,
        {'irc_token': request.user.irc_token},
        session=request.state.db
    )

    return IrcTokenResponse(
        username=request.user.name.replace(' ', '_'),
        token=request.user.irc_token
    )
