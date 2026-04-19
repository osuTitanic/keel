
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.models import TokenResponse, ErrorResponse
from app.security import require_login, TokenSource
from app.common.database import DBUser
from app.utils import requires

import app.security as security

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
    token = security.issue_api_token_pair(
        request.user,
        request.state.redis,
        TokenSource.Api
    )
    token_response = TokenResponse(**token)

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
    authorization = request.headers.get("Authorization", "")
    if " " not in authorization:
        raise HTTPException(403, detail="Invalid token provided")

    scheme, token = authorization.split(" ", 1)
    if scheme.lower() != "bearer":
        raise HTTPException(403, detail="Invalid token provided")

    claims = security.validate_refresh_token(token, request.state.redis)
    if not claims:
        raise HTTPException(403, detail="Invalid token provided")

    token = security.issue_api_token_pair(
        request.user,
        request.state.redis,
        TokenSource.Api
    )
    token_response = TokenResponse(**token)
    security.delete_api_session(claims, request.state.redis)

    response = JSONResponse(
        content=token_response.model_dump(),
        media_type='application/json'
    )
    return response
