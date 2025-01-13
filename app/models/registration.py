
from config import RECAPTCHA_SECRET_KEY, RECAPTCHA_SITE_KEY
from pydantic import BaseModel, field_validator

class RegistrationRequestModel(BaseModel):
    username: str
    password: str
    email: str
    recaptcha_response: str | None

    @field_validator('recaptcha_response')
    def validate_recaptcha(cls, value: str | None):
        if not RECAPTCHA_SECRET_KEY or not RECAPTCHA_SITE_KEY:
            return

        if not value:
            raise ValueError('Recaptcha response is required')

class RegistrationResponseModel(BaseModel):
    user_id: int
    verification_id: int | None

class ValidationRequestModel(BaseModel):
    type: str
    value: str

class ValidationResponseModel(BaseModel):
    valid: bool
    message: str | None = None
