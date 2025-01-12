
from __future__ import annotations
from app.common.helpers import ip
from app.models import ErrorResponse
from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Callable
from redis import Redis

import asyncio
import config
import app

async def run_async(func: Callable, *args):
    return await asyncio.get_event_loop().run_in_executor(
        None, func, *args
    )

def error_response(status_code: int, detail: str):
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=status_code, details=detail).model_dump()
    )

async def ratelimit_middleware(request: Request, call_next: Callable):
    ip_address = ip.resolve_ip_address_fastapi(request)
    redis: Redis = request.state.redis

    # Get current request count
    current = await run_async(redis.get, f'ratelimit:{ip_address}') or b'0'

    # Check for rate limit
    if int(current) > config.API_RATELIMIT_LIMIT:
        return error_response(429, 'Rate limit exceeded')

    # Set the new request count with expiry
    await run_async(
        redis.setex, f'ratelimit:{ip_address}',
        config.API_RATELIMIT_WINDOW, int(current) + 1
    )

    # TODO: Implement different ratelimiting levels based on groups
    return await call_next(request)

if config.API_RATELIMIT_ENABLED:
    app.api.middleware("http")(ratelimit_middleware)
