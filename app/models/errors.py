
from __future__ import annotations
from pydantic import BaseModel
from typing import List, Sequence

class ErrorResponse(BaseModel):
    error: int
    details: str

class ValidationErrorModel(BaseModel):
    loc: Sequence[str]
    msg: str
    type: str
    input: str | None

class ValidationErrorResponse(BaseModel):
    error: int = 400
    details: str = "Validation Error"
    errors: List[ValidationErrorModel]
