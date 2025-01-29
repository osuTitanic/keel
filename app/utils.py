
from fastapi import HTTPException, Request
from typing import Callable, Generator
from PIL import Image

import functools
import inspect
import asyncio
import typing
import io

async def run_async(func: Callable, *args):
    return await asyncio.get_event_loop().run_in_executor(
        None, func, *args
    )

def file_iterator(file: bytes, chunk_size: int = 1024) -> Generator[bytes, None, None]:
    offset = 0

    while offset < len(file):
        yield file[offset:offset + chunk_size]
        offset += chunk_size

def resolve_request(func: typing.Callable, *args, **kwargs) -> Request:
    signature = inspect.signature(func)

    if 'request' in signature.parameters:
        bound_arguments = signature.bind_partial(*args, **kwargs)
        return bound_arguments.arguments.get('request')

def resize_image(
    image: bytes,
    target_width: int | None = None,
    target_height: int | None = None
) -> bytes:
    image_buffer = io.BytesIO()
    img = Image.open(io.BytesIO(image))
    img = img.resize((target_width, target_height))
    img.save(image_buffer, format='JPEG')
    return image_buffer.getvalue()

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

            if request.user.is_authenticated and request.user.is_admin:
                return await func(*args, **kwargs)

            if not any(scope in request.auth.scopes for scope in scopes_list):
                raise HTTPException(status_code, detail=message)

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            request = resolve_request(func, *args, **kwargs)

            if not request:
                raise ValueError("The function does not have a request parameter")

            if request.user.is_authenticated and request.user.is_admin:
                return func(*args, **kwargs)

            if not any(scope in request.auth.scopes for scope in scopes_list):
                raise HTTPException(status_code, detail=message)

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
