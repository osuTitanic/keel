
from fastapi import HTTPException, APIRouter, Request
from redis.asyncio import Redis

from app.models import CSRFTokenResponse, ErrorResponse
from app.security import require_login
from app.utils import requires

# TODO: Reject endpoint for OAuth2
router = APIRouter(
    responses={
        403: {'model': ErrorResponse, 'description': 'Invalid token provided'},
        401: {'model': ErrorResponse, 'description': 'Authentication failure'},
    },
    dependencies=[require_login]
)

@router.get("/csrf", response_model=CSRFTokenResponse)
@requires("users.authenticated")
async def get_csrf_token(request: Request) -> CSRFTokenResponse:
    """Get the current CSRF token for the authenticated user."""
    redis: Redis = request.state.redis_async
    stored_token = await redis.get(f"csrf:{request.user.id}")

    if not stored_token:
        raise HTTPException(
            status_code=403,
            detail="No CSRF token found for user"
        )

    return CSRFTokenResponse(token=stored_token)
