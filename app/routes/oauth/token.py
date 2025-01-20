
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import JSONResponse, Response
from app.models import TokenResponse, ErrorResponse
from app.common.database import DBUser, users
from app.security import require_login

import app.security as security
import config
import time

router = APIRouter(
    responses={
        403: {'model': ErrorResponse, 'description': 'Invalid refresh token'},
        401: {'model': ErrorResponse, 'description': 'Authentication failure'},
    },
    dependencies=[require_login]
)

def validate_refresh_token(request: Request) -> DBUser:
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        raise HTTPException(status_code=401, detail='No refresh token provided')

    data = security.validate_token(refresh_token)

    if not data:
        raise HTTPException(status_code=401, detail='Invalid refresh token')

    return users.fetch_by_id(data['id'])

@router.post("/token", response_model=TokenResponse)
def generate_token(request: Request) -> Response:
    user: DBUser = request.user

    if "authenticated" not in request.auth.scopes:
        # Try to authenticate user through refresh token
        user = validate_refresh_token(request)

    current_time = time.time()
    expiry = round(current_time) + config.FRONTEND_TOKEN_EXPIRY
    expiry_refresh = round(current_time) + config.FRONTEND_REFRESH_EXPIRY

    # Generate new access & refresh tokens
    access_token = security.generate_token(user, expiry)
    refresh_token = security.generate_token(user, expiry_refresh)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expiry,
        token_type='Bearer',
    )

    response = JSONResponse(
        content=token_response.model_dump(),
        media_type='application/json'
    )

    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=config.FRONTEND_REFRESH_EXPIRY,
        httponly=True,
        secure=config.ENABLE_SSL,
        samesite='strict',
        domain=f".{config.DOMAIN_NAME}"
    )

    return response
