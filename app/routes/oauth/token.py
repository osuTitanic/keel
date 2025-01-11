
from starlette.authentication import requires
from fastapi import APIRouter, Request
from app.models import TokenResponse

import app.security as security
import config
import time

router = APIRouter()

@router.post("/token", response_model=TokenResponse)
@requires('authenticated')
def generate_token(request: Request) -> TokenResponse:
    expiry = round(time.time() + config.FRONTEND_TOKEN_EXPIRY)
    token = security.generate_token(request.user, expiry)
    return TokenResponse(
        access_token=token,
        expires_in=expiry,
        token_type='bearer',
    )
