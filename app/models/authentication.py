
from __future__ import annotations
from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = 'bearer'
