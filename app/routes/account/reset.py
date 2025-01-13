
from __future__ import annotations
from fastapi import HTTPException, APIRouter, Request

from app.models import VerificationResponseModel, PasswordResetRequestModel
from app.common.database import users, verifications
from app.common import mail

import config

router = APIRouter()

@router.post('/reset', response_model=VerificationResponseModel)
def password_reset(
    request: Request,
    reset: PasswordResetRequestModel
) -> VerificationResponseModel:
    if not config.EMAILS_ENABLED:
        raise HTTPException(503, 'Password resets are not enabled at the moment. Please contact an administrator!')

    if not (user := users.fetch_by_email(reset.email, request.state.db)):
        raise HTTPException(404, 'We could not find any user with that email address.')

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

    return VerificationResponseModel(
        user_id=user.id,
        verification_id=verification.id
    )
