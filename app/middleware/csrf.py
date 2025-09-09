
from fastapi.responses import JSONResponse
from app.models import ErrorResponse
from redis.asyncio import Redis
from typing import Callable
from fastapi import Request
from app import api

@api.middleware("http")
async def csrf_middleware(request: Request, call_next: Callable):
    if not request.user:
        return await call_next(request)

    if not (csrf_token := request.headers.get("x-csrf-token")):
        return await call_next(request)

    redis: Redis = request.state.redis_async
    stored_token = await redis.get(f"csrf:{request.user.id}")

    if not stored_token:
        return await call_next(request)

    if stored_token != csrf_token:
        return error_response(403, "Invalid CSRF token")

    return await call_next(request)

def error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=status_code, details=detail).model_dump()
    )
