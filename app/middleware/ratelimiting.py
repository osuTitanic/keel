
from fastapi.responses import JSONResponse
from typing import Callable, Tuple
from fastapi import Request
from redis import Redis

from app.models import ErrorResponse
from app.common.helpers import ip
from app.common import officer
from app import utils

import config
import app

async def ratelimit_middleware(request: Request, call_next: Callable):
    ip_address = ip.resolve_ip_address_fastapi(request)

    if ip.is_local_ip(ip_address):
        # Skip rate limiting for local IPs
        return await call_next(request)

    redis: Redis = request.state.redis
    key = f'ratelimit:{ip_address}'

    # Get ratelimit configuration
    window, limit = resolve_ratelimit_configuration(request)

    # Get current request count
    current = await utils.run_async(redis.get, key)

    if current is None:
        # If the key doesn't exist, set to 1 and start the expiration timer
        await utils.run_async(redis.setex, key, window, 1)
        return await call_next(request)

    # Check for rate limit
    if int(current) > limit:
        return error_response(429, 'Rate limit exceeded')

    # Increment the request count
    await utils.run_async(redis.incr, key)

    if int(current) + 1 >= limit:
        await utils.run_async(
            officer.call,
            f"{ip_address} has exceeded the api ratelimit of "
            f"{limit} requests / {window} seconds."
        )

        # Reset expiration timer
        await utils.run_async(redis.expire, key, window)
        return error_response(429, 'Rate limit exceeded')

    return await call_next(request)

def resolve_ratelimit_configuration(request: Request) -> Tuple[int, int]:
    if "admin" in request.auth.scopes:
        return (
            config.API_RATELIMIT_WINDOW,
            69420 # let's hope that's enough :)
        )

    if "authenticated" in request.auth.scopes:
        return (
            config.API_RATELIMIT_WINDOW,
            config.API_RATELIMIT_AUTHENTICATED
        )

    return (
        config.API_RATELIMIT_WINDOW,
        config.API_RATELIMIT_REGULAR
    )

def error_response(status_code: int, detail: str):
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=status_code, details=detail).model_dump()
    )

if config.API_RATELIMIT_ENABLED:
    app.api.middleware("http")(ratelimit_middleware)
