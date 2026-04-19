
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.common.config import config_instance as config
from app.models import TokenResponse, ErrorResponse
from app.security import require_login, TokenSource
from app.common.database import DBUser
from app.utils import requires

import app.security as security
import time

# TODO: Reject endpoints for OAuth2
router = APIRouter(
    responses={
        403: {'model': ErrorResponse, 'description': 'Invalid token provided'},
        401: {'model': ErrorResponse, 'description': 'Authentication failure'},
    },
    dependencies=[require_login]
)

@router.post("/login", response_model=TokenResponse)
@requires("users.authenticated")
def generate_access_token(request: Request) -> JSONResponse:
    """Request an access token to access authenticated routes, and have higher rate limits.

    You are able to authenticate using a `Basic` authenticaton header, or a `Bearer` token.
    To use the refresh token, please view the `/refresh` endpoint.

    Currently, this is the only authentication method available. A full OAuth2 implementation
    is planned for the future.
    """
    user: DBUser = request.user

    current_time = round(time.time())
    expiry = current_time + config.FRONTEND_TOKEN_EXPIRY
    expiry_refresh = current_time + config.FRONTEND_REFRESH_EXPIRY

    # Generate new access & refresh tokens
    access_token = security.generate_token(user, expiry, TokenSource.Api)
    refresh_token = security.generate_token(user, expiry_refresh, TokenSource.Api)

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
    return response

@router.post("/refresh", response_model=TokenResponse)
@requires("users.authenticated")
def refresh_access_token(request: Request) -> JSONResponse:
    """Request a new access token using the refresh token.

    This endpoint is used to refresh the access token after it has expired
    through an explicit authenticated API request.
    """
    user: DBUser = request.user

    current_time = round(time.time())
    expiry = current_time + config.FRONTEND_TOKEN_EXPIRY
    expiry_refresh = current_time + config.FRONTEND_REFRESH_EXPIRY

    # Generate new access & refresh tokens
    access_token = security.generate_token(user, expiry, TokenSource.Api)
    refresh_token = security.generate_token(user, expiry_refresh, TokenSource.Api)

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
    return response
