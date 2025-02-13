
from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Callable
from redis import Redis

from app.models import ErrorResponse
from app.common.helpers import ip
from app.common import officer
from app import utils

import config
import app

def error_response(status_code: int, detail: str):
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=status_code, details=detail).model_dump()
    )

async def ratelimit_middleware(request: Request, call_next: Callable):
    ip_address = ip.resolve_ip_address_fastapi(request)
    redis: Redis = request.state.redis

    # Get current request count
    current = await utils.run_async(redis.get, f'ratelimit:{ip_address}')

    if not current:
        # If the key doesn't exist, set to 1 and start the expiration timer
        await utils.run_async(
            redis.setex, f'ratelimit:{ip_address}',
            config.API_RATELIMIT_WINDOW, 1
        )
        return await call_next(request)

    # Check for rate limit
    if int(current) > config.API_RATELIMIT_LIMIT:
        return error_response(429, 'Rate limit exceeded')

    # Increment the request count
    await utils.run_async(redis.incr, f'ratelimit:{ip_address}')

    if int(current) + 1 >= config.API_RATELIMIT_LIMIT:
        await utils.run_async(
            officer.call,
            f"{ip_address} has exceeded the api ratelimit of "
            f"{config.API_RATELIMIT_LIMIT} requests / {config.API_RATELIMIT_WINDOW} seconds."
        )

    # TODO: Implement different ratelimiting levels based on groups
    return await call_next(request)

if config.API_RATELIMIT_ENABLED:
    app.api.middleware("http")(ratelimit_middleware)
