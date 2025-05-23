
from fastapi import HTTPException, APIRouter, Request

from app.models import VerificationResponse, PasswordResetRequest, ErrorResponse
from app.common.database import users, verifications
from app.common import mail

import config

router = APIRouter(
    responses={
        503: {'description': 'Password resets are disabled', 'model': ErrorResponse},
        404: {'description': 'User not found', 'model': ErrorResponse}
    }
)

@router.post("/reset", response_model=VerificationResponse)
def password_reset(
    request: Request,
    reset: PasswordResetRequest
) -> VerificationResponse:
    """Request a password reset for a user account"""
    if not config.EMAILS_ENABLED:
        raise HTTPException(503, 'Password resets are not enabled at the moment. Please contact an administrator!')

    if not (user := users.fetch_by_email(reset.email, request.state.db)):
        raise HTTPException(404, 'We could not find any user with that email address.')
    
    lock = request.state.redis.get(f'reset_lock:{user.id}') or b'0'

    if int(lock):
        raise HTTPException(503, 'You have already requested a password reset. Please check your email.')

    request.state.logger.info(
        'Sending verification email for resetting password...'
    )

    verification = verifications.create(
        user.id,
        type=1,
        token_size=32,
        session=request.state.db
    )

    mail.send_password_reset_email(
        verification,
        user
    )

    # Set a lock for the user to prevent spamming
    request.state.redis.set(f'reset_lock:{user.id}', 1, ex=3600*12)

    return VerificationResponse(
        user_id=user.id,
        verification_id=verification.id
    )
