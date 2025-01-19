
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from .models import ErrorResponse, ValidationErrorResponse, ValidationErrorModel
from .server import api

import config

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

@api.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = ValidationErrorResponse(
        errors=[
            ValidationErrorModel(
                loc=error['loc'],
                msg=error['msg'],
                type=error['type'],
                input=str(error.get('input', '')) or None
            )
            for error in exc.errors()
        ]
    )

    return JSONResponse(
        response.model_dump(),
        status_code=400
    )

@api.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    if config.DEBUG:
        raise exc

    return JSONResponse(
        ErrorResponse(
            error=500,
            details="Internal Server Error"
        ).model_dump(),
        status_code=500
    )
