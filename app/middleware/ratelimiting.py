
from fastapi.responses import JSONResponse
from fastapi import Request, Response
from typing import Callable, Tuple
from redis.asyncio import Redis

from app.models import ErrorResponse
from app.common.helpers import ip
from app.common import officer
from app import utils

import config
import time
import app

async def ratelimit_middleware(request: Request, call_next: Callable) -> Response:
    ip_address = ip.resolve_ip_address_fastapi(request)
    request.state.is_local_ip = ip.is_local_ip(ip_address)

    if request.state.is_local_ip:
        # Skip rate limiting for local IPs
        return await call_next(request)

    redis: Redis = request.state.redis_async
    counter_key = f'ratelimit:{ip_address}'
    ttl_key = f'ratelimit:{ip_address}:ttl'

    # Get ratelimit configuration based on auth scopes
    window, limit = resolve_ratelimit_configuration(request)

    # Increment request count
    current = await redis.incr(counter_key)
    current_time = int(time.time())

    if current == 1:
        # First request in this window, set expiration and store reset time
        await redis.expire(counter_key, window)
        await redis.setex(ttl_key, window, current_time + window)

    reset_time = int(await redis.get(ttl_key) or b'0')

    if not reset_time:
        # Fallback if ttl key is missing
        reset_time = current_time + window
        await redis.setex(ttl_key, window, reset_time)

    # Calculate remaining requests & check if rate limit is exceeded
    remaining = max(0, limit - current)

    if current > limit:
        await utils.run_async(
            officer.call,
            f"{ip_address} has exceeded the api ratelimit of "
            f"{limit} requests / {window} seconds."
        )
        return error_response(
            429, 'Rate limit exceeded',
            limit, remaining, reset_time
        )

    # Process the request and add rate limit headers to response
    response = await call_next(request)
    response.headers['X-RateLimit-Limit'] = str(limit)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(reset_time)
    return response

def resolve_ratelimit_configuration(request: Request) -> Tuple[int, int]:
    if "admin" in request.auth.scopes:
        return (
            config.API_RATELIMIT_WINDOW,
            69420 # let's hope that's enough :)
        )

    if "users.authenticated" in request.auth.scopes:
        return (
            config.API_RATELIMIT_WINDOW,
            config.API_RATELIMIT_AUTHENTICATED
        )

    return (
        config.API_RATELIMIT_WINDOW,
        config.API_RATELIMIT_REGULAR
    )

def error_response(
    status_code: int,
    detail: str,
    limit: int = 0,
    remaining: int = 0,
    reset: int = 0
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=status_code, details=detail).model_dump()
    )

    if limit > 0:
        # Add rate limit headers even on error responses
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(reset)

    return response

if config.API_RATELIMIT_ENABLED:
    app.api.middleware("http")(ratelimit_middleware)
