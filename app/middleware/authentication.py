
from __future__ import annotations
from starlette.authentication import AuthenticationBackend, AuthCredentials, UnauthenticatedUser
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection
from typing import List

from app.common.database.repositories import users, groups
from app.common.database import DBUser
from app import api

import app.security as security
import logging
import asyncio
import base64

class AuthBackend(AuthenticationBackend):
    def __init__(self):
        self.logger = logging.getLogger('authentication')

    async def authenticate(self, request: HTTPConnection):
        if not (auth_header := request.headers.get('Authorization')):
            return AuthCredentials([]), UnauthenticatedUser()

        authorization = await self.parse_authorization(auth_header)

        validators = {
            'basic': self.basic_authentication,
            'bearer': self.token_authentication
        }

        if authorization['scheme'] not in validators:
            self.logger.warning(f'Invalid authorization scheme: {authorization["scheme"]}')
            return AuthCredentials([]), UnauthenticatedUser()

        try:
            validator = validators[authorization['scheme']]
            user: DBUser = await validator(authorization['data'])
        except Exception as e:
            self.logger.error(f'Authentication failure ({authorization["scheme"]}): {e}')
            return AuthCredentials([]), UnauthenticatedUser()

        if not user:
            return AuthCredentials([]), UnauthenticatedUser()

        scopes = ['authenticated']

        if user.activated:
            scopes.append('activated')

        for group in await self.fetch_user_groups(user.id):
            scopes.append(group.lower())

        return AuthCredentials(scopes), user
    
    async def basic_authentication(self, data: str) -> DBUser | None:
        username, password = base64.b64decode(data).decode().split(':', 1)
        loop = asyncio.get_event_loop()

        user: DBUser = await loop.run_in_executor(
            None, users.fetch_by_name_case_insensitive, username
        )

        if not user:
            return None

        is_correct = await security.password_authentication_async(
            password, user.bcrypt
        )

        if not is_correct:
            return None

        return user

    async def token_authentication(self, token: str) -> DBUser | None:
        data = security.decode_token(token)

        if not data:
            return None

        return await asyncio.get_event_loop().run_in_executor(
            None, users.fetch_by_id, data['id']
        )

    async def fetch_user_groups(self, user_id: int) -> List[str]:
        user_groups = await asyncio.get_event_loop().run_in_executor(
            None, groups.fetch_user_groups,
            user_id, True
        )
        return [group.name for group in user_groups]

    async def parse_authorization(self, authorization: str) -> dict[str, str]:
        if ' ' not in authorization:
            return {'scheme': '', 'data': ''}

        scheme, data = authorization.split(' ', 1)
        return {'scheme': scheme.lower(), 'data': data}

api.add_middleware(AuthenticationMiddleware, backend=AuthBackend())
