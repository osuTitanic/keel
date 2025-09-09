
from fastapi.responses import JSONResponse
from app.models import ErrorResponse
from redis.asyncio import Redis
from config import DOMAIN_NAME
from typing import Callable
from fastapi import Request
from app import api

@api.middleware("http")
async def csrf_middleware(request: Request, call_next: Callable):
    if not request.user.is_authenticated:
        return await call_next(request)

    osu_domain = f"osu.{DOMAIN_NAME}"
    requires_csrf = osu_domain in request.headers.get("Origin", "")

    if not requires_csrf:
        return await call_next(request)

    is_valid = await is_valid_token(request)

    if requires_csrf and not is_valid:
        return error_response(403, "Invalid CSRF token")

    return await call_next(request)

async def is_valid_token(request: Request) -> bool:
    if not (csrf_token := request.headers.get("x-csrf-token")):
        return False

    redis: Redis = request.state.redis_async
    stored_token = await redis.get(f"csrf:{request.user.id}")

    if not stored_token:
        return False

    if stored_token != csrf_token:
        return False

    return True

def error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=status_code, details=detail).model_dump()
    )
