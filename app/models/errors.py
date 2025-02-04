
from typing import Any, List, Sequence
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: int
    details: str

class ValidationErrorModel(BaseModel):
    loc: Sequence[Any]
    msg: Any
    type: Any
    input: Any | None

class ValidationErrorResponse(BaseModel):
    error: int = 400
    details: str = "Validation Error"
    errors: List[ValidationErrorModel]
