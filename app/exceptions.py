
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from .models import ErrorResponse, ValidationErrorResponse
from .server import api

@api.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        ValidationErrorResponse(
            errors=exc.errors()
        ).model_dump(),
        status_code=400
    )

@api.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        ErrorResponse(
            error=exc.status_code,
            details=exc.detail
        ).model_dump(),
        status_code=exc.status_code
    )

@api.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        ErrorResponse(
            error=exc.status_code,
            details=exc.detail
        ).model_dump(),
        status_code=exc.status_code
    )
