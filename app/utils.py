
from app.common.database.repositories import wrapper
from app.common.database import stats, histories
from app.common.database.objects import DBUser
from app.common.helpers import permissions
from app.common.cache import leaderboards

from typing import Callable, Generator, Tuple
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from itertools import tee
from PIL import Image

import app.session
import functools
import inspect
import asyncio
import typing
import config
import io

async def run_async(func: Callable, *args):
    return await asyncio.get_event_loop().run_in_executor(
        None, func, *args
    )

def resolve_request(func: typing.Callable, *args, **kwargs) -> Request:
    signature = inspect.signature(func)

    if 'request' in signature.parameters:
        bound_arguments = signature.bind_partial(*args, **kwargs)
        return bound_arguments.arguments.get('request')

def is_empty_generator(generator: Generator) -> Tuple[bool, Generator]:
    try:
        generator, copy = tee(generator)
        next(copy)
    except StopIteration:
        return True, generator

    return False, generator

def resize_image(
    image: bytes,
    target_width: int | None = None,
    target_height: int | None = None
) -> io.BytesIO:
    image_buffer = io.BytesIO()
    img = Image.open(io.BytesIO(image))
    img = img.resize((target_width, target_height))
    img.save(image_buffer, format='JPEG')
    image_buffer.seek(0)
    return image_buffer

def on_sync_ranks_fail(e: Exception) -> None:
    app.session.logger.error(
        f'Failed to update user rank: {e}',
        exc_info=e
    )

@wrapper.exception_wrapper(on_sync_ranks_fail)
def sync_ranks(user: DBUser, session: Session) -> None:
    for user_stats in user.stats:
        if user_stats.playcount <= 0:
            continue

        global_rank = leaderboards.global_rank(
            user.id,
            user_stats.mode
        )

        if user_stats.rank == global_rank:
            continue

        # Database rank desynced from redis
        stats.update(
            user.id,
            user_stats.mode,
            {'rank': global_rank},
            session=session
        )
        user_stats.rank = global_rank

        if not config.FROZEN_RANK_UPDATES:
            # Update rank history
            histories.update_rank(
                user_stats,
                user.country,
                session=session
            )

def requires(
    scopes: str | typing.Sequence[str],
    status_code: int = 403,
    message: str = "You are not authorized to perform this action"
) -> typing.Callable[[typing.Callable], typing.Callable]:
    """This function checks if the user is either an admin, or has the required scope(s)"""
    scopes_list = [scopes] if isinstance(scopes, str) else list(scopes)

    def decorator(func: typing.Callable) -> typing.Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            request = resolve_request(func, *args, **kwargs)

            if not request:
                raise ValueError("The function does not have a request parameter")

            if request.user.is_authenticated:
                if request.user.is_admin:
                    return func(*args, **kwargs)

                if any(permissions.is_rejected(scope, request.user.id) for scope in scopes_list):
                    raise HTTPException(status_code, detail=message)

            if not any(scope in request.auth.scopes for scope in scopes_list):
                raise HTTPException(status_code, detail=message)

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            request = resolve_request(func, *args, **kwargs)

            if not request:
                raise ValueError("The function does not have a request parameter")

            if request.user.is_authenticated:
                if request.user.is_admin:
                    return func(*args, **kwargs)

                if any(permissions.is_rejected(scope, request.user.id) for scope in scopes_list):
                    raise HTTPException(status_code, detail=message)

            if not any(scope in request.auth.scopes for scope in scopes_list):
                raise HTTPException(status_code, detail=message)

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
