
from fastapi import HTTPException, APIRouter, Request
from sqlalchemy.orm import Session

from app.common.constants.notifications import NotificationType
from app.common.constants.regexes import USERNAME, EMAIL
from app.common.constants.strings import BAD_WORDS
from app.common.helpers import ip, location
from app.common import officer, mail
from app.models import (
    VerificationResponse,
    RegistrationRequest,
    ValidationResponse,
    ValidationRequest,
    ErrorResponse
)

from app.common.database import (
    verifications,
    notifications,
    groups,
    users,
    names,
)

import hashlib
import bcrypt
import config

router = APIRouter()

registration_errors = {
    403: {'model': ErrorResponse, 'description': 'One account should be enough'},
    400: {'model': ErrorResponse, 'description': 'Invalid request data'},
    429: {'model': ErrorResponse, 'description': 'Too many registrations from this ip'},
    500: {'model': ErrorResponse, 'description': 'Failed to process the registration'}
}

validation_errors = {
    400: {'model': ErrorResponse, 'description': 'Invalid validation type'}
}

@router.post("/register", response_model=VerificationResponse, responses=registration_errors)
def user_registration(
    request: Request,
    registration: RegistrationRequest
) -> VerificationResponse:
    """Register a new user account"""
    if "authenticated" in request.auth.scopes:
        raise HTTPException(
            status_code=403,
            detail='One account should be enough'
        )

    if (error := validate_username(registration.username, request.state.db)):
        raise HTTPException(status_code=400, detail=error)

    if (error := validate_email(registration.email, request.state.db)):
        raise HTTPException(status_code=400, detail=error)

    if (error := validate_password(registration.password, request.state.db)):
        raise HTTPException(status_code=400, detail=error)

    ip_address = ip.resolve_ip_address_fastapi(request)
    registration_count = int(request.state.redis.get(f'registrations:{ip_address}') or b'0')

    if registration_count > 2:
        officer.call(
            f'Failed to register: Too many registrations from ip ({ip_address})'
        )
        raise HTTPException(
            status_code=429,
            detail='There have been too many registrations from this ip. Please try again later!'
        )

    if config.RECAPTCHA_SECRET_KEY and config.RECAPTCHA_SITE_KEY:
        response = request.state.requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': config.RECAPTCHA_SECRET_KEY,
                'response': registration.recaptcha_response,
                'remoteip': ip_address
            }
        )

        if not response.ok:
            raise HTTPException(400, 'Failed to verify captcha response!')

        if not response.json().get('success', False):
            raise HTTPException(400, 'Captcha verification failed!')

    request.state.logger.info(
        f'Starting registration process for '
        f'"{registration.username}" ({registration.email}) ({ip_address})...'
    )

    geolocation = location.fetch_web(ip_address)
    country = geolocation.country_code.upper() if geolocation else 'XX'
    cf_country = request.headers.get('CF-IPCountry', 'XX')

    if cf_country not in ('XX', 'T1'):
        country = cf_country.upper()

    pw_bcrypt = hashed_password(registration.password)
    username = registration.username.strip()
    safe_name = username.lower().replace(' ', '_')

    user = users.create(
        username=username,
        safe_name=safe_name,
        email=registration.email.lower(),
        pw_bcrypt=pw_bcrypt,
        country=country,
        activated=False if config.EMAILS_ENABLED else True,
        session=request.state.db
    )

    if not user:
        officer.call(f'Failed to register user "{username}".')
        raise HTTPException(500, 'Failed to process the registration. Please try again later.')
    
    request.state.logger.info(
        f'User "{username}" with id "{user.id}" was created.'
    )

    # Send welcome notification
    notifications.create(
        user.id,
        NotificationType.Welcome.value,
        'Welcome!',
        'Welcome aboard! '
        f'Get started by downloading one of our builds [here]({config.OSU_BASEURL}/download). '
        'Enjoy your journey!',
        session=request.state.db
    )

    # Add user to players & supporters group
    groups.create_entry(user.id, 999, session=request.state.db)
    groups.create_entry(user.id, 1000, session=request.state.db)

    # Increment registration count
    request.state.redis.incr(f'registrations:{ip_address}')
    request.state.redis.expire(f'registrations:{ip_address}', 3600 * 24)

    if not config.EMAILS_ENABLED:
        # Verification is disabled
        request.state.logger.info('Registration finished.')
        return VerificationResponse(
            user_id=user.id,
            verification_id=None
        )
    
    request.state.logger.info('Sending verification email...')

    verification = verifications.create(
        user.id,
        type=0,
        token_size=32,
        session=request.state.db
    )

    mail.send_welcome_email(verification, user)
    request.state.logger.info('Registration finished.')

    return VerificationResponse(
        user_id=user.id,
        verification_id=verification.id
    )

@router.get("/register/check", response_model=ValidationResponse, responses=validation_errors)
def user_registration_validation(
    request: Request,
    validation: ValidationRequest
) -> ValidationResponse:
    """Validate a username, email, or password for the registration"""
    validators = {
        'username': validate_username,
        'email': validate_email,
        'password': validate_password
    }

    if error := validators[validation.type](validation.value, request.state.db):
        return ValidationResponse(
            valid=False,
            message=error
        )

    return ValidationResponse(valid=True)

def validate_username(username: str, session: Session) -> str | None:
    username = username.strip()

    if len(username) < 3:
        return "Your username is too short."

    if len(username) > 25:
        return "Your username is too long."

    if not USERNAME.match(username):
        return "Your username contains invalid characters."

    if any(word in username.lower() for word in BAD_WORDS):
        return "Your username contains offensive words."

    if username.lower().startswith('deleteduser'):
        return "This username is not allowed."

    if username.lower().endswith('_old'):
        return "This username is not allowed."

    safe_name = username.lower().replace(' ', '_')

    if users.fetch_by_safe_name(safe_name, session=session):
        return "This username is already in use!"

    if names.fetch_by_name_extended(username, session=session):
        return "This username is already in use!"

def validate_email(email: str, session: Session) -> str | None:
    if not EMAIL.match(email):
        return "Please enter a valid email address!"

    if users.fetch_by_email(email.lower(), session):
        return "This email address is already in use."

def validate_password(password: str, session: Session) -> str | None:
    if len(password) < 8:
        return "Please enter a password with at least 8 characters!"

    if len(password) > 255:
        return "Woah there! That password is a bit too long, don't you think?"

def hashed_password(password: str) -> str:
    md5_hash = hashlib.md5(password.encode()) \
        .hexdigest() \
        .encode()

    return bcrypt.hashpw(md5_hash, bcrypt.gensalt()).decode()
