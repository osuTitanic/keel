
from fastapi import HTTPException, Request

import functools
import inspect
import asyncio
import typing

def resolve_request(func: typing.Callable, *args, **kwargs) -> Request:
    signature = inspect.signature(func)

    if 'request' in signature.parameters:
        bound_arguments = signature.bind_partial(*args, **kwargs)
        return bound_arguments.arguments.get('request')

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
