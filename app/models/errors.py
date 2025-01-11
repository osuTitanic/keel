
from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Sequence

class ErrorResponse(BaseModel):
    error: int
    details: str

class ValidationErrorResponse(BaseModel):
    error: int = 400
    details: str = "Validation Error"
    errors: Sequence[Any]
