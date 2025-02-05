
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

@router.post("/login", response_model=TokenResponse)
def generate_authentication_token(request: Request) -> Response:
    """Request an access token to access authenticated routes, and have higher rate limits.

    You are able to authenticate using a `Basic` authenticaton header, or a `Bearer` token.
    To use the refresh token, you just have to pass it as a cookie in the request, which will
    then take priority over the `Authorization` header.

    Currently, this is the only authentication method available. A full OAuth2 implementation
    is planned for the future.
    """
    user: DBUser = request.user

    if "authenticated" not in request.auth.scopes:
        # Try to authenticate user through refresh token
        user = validate_browser_session(request)

    current_time = round(time.time())
    expiry = current_time + config.FRONTEND_TOKEN_EXPIRY
    expiry_refresh = current_time + config.FRONTEND_REFRESH_EXPIRY

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
        key='access_token',
        value=access_token,
        max_age=config.FRONTEND_TOKEN_EXPIRY,
        httponly=True,
        secure=config.ENABLE_SSL,
        samesite='strict',
        domain=f".{config.DOMAIN_NAME}"
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

def validate_browser_session(request: Request) -> DBUser:
    """Validate the user's session through the browser's cookies."""
    data = (
        validate_access_token(request) or
        validate_refresh_token(request)
    )

    if not data:
        raise HTTPException(
            status_code=401,
            detail='Authentication failure'
        )

    return users.fetch_by_id(data['id'])

def validate_access_token(request: Request) -> DBUser:
    access_token = request.cookies.get('access_token')

    if not access_token:
        return

    data = security.validate_token(access_token)

    if not data:
        raise HTTPException(status_code=401, detail='Invalid access token')
    
    return data

def validate_refresh_token(request: Request) -> DBUser:
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        return

    data = security.validate_token(refresh_token)

    if not data:
        raise HTTPException(status_code=401, detail='Invalid refresh token')
    
    return data
