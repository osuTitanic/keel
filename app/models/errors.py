
from __future__ import annotations
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: int
    details: str
