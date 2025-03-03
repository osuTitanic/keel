
from starlette.authentication import AuthenticationBackend, AuthCredentials, UnauthenticatedUser
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection
from typing import List

from app.common.database.repositories import users, groups
from app.common.database import DBUser
from app import api, utils

import app.security as security
import logging
import base64

class AuthBackend(AuthenticationBackend):
    def __init__(self):
        self.logger = logging.getLogger('authentication')

    async def authenticate(self, request: HTTPConnection):
        if (access_token := request.cookies.get('access_token')):
            # Use access_token cookie to authenticate user
            user = await self.token_authentication(access_token, request)
            scopes = await self.resolve_user_scopes(user, request)
            return AuthCredentials(scopes), user

        if not (auth_header := request.headers.get('Authorization')):
            return AuthCredentials([]), UnauthenticatedUser()

        validators = {
            'basic': self.basic_authentication,
            'bearer': self.token_authentication
        }

        # Use Authorization header to authenticate user
        authorization = self.parse_authorization(auth_header)

        if authorization['scheme'] not in validators:
            self.logger.warning(f'Invalid authorization scheme: {authorization["scheme"]}')
            return AuthCredentials([]), UnauthenticatedUser()

        try:
            validator = validators[authorization['scheme']]
            user: DBUser = await validator(authorization['data'], request)
        except Exception as e:
            self.logger.error(f'Authentication failure ({authorization["scheme"]}): {e}', exc_info=True)
            return AuthCredentials([]), UnauthenticatedUser()

        if not user:
            self.logger.warning(f'Invalid credentials for {authorization["scheme"]}')
            return AuthCredentials([]), UnauthenticatedUser()

        scopes = await self.resolve_user_scopes(user, request)
        return AuthCredentials(scopes), user

    async def basic_authentication(self, data: str, request: HTTPConnection) -> DBUser | None:
        username, password = base64.b64decode(data).decode().split(':', 1)

        user: DBUser = await utils.run_async(
            users.fetch_by_name_case_insensitive,
            username, request.state.db
        )

        if not user:
            return None

        is_correct = await security.password_authentication_async(
            password, user.bcrypt
        )

        if not is_correct:
            return None

        return user

    async def token_authentication(self, token: str, request: HTTPConnection) -> DBUser | None:
        data = security.validate_token(token)

        if not data:
            return None

        return await utils.run_async(
            users.fetch_by_id_no_options,
            data['id'], request.state.db
        )

    async def fetch_user_groups(self, user_id: int, request: HTTPConnection) -> List[str]:
        user_groups = await utils.run_async(
            groups.fetch_user_groups,
            user_id, True, request.state.db
        )
        return [group.short_name for group in user_groups]
    
    async def resolve_user_scopes(self, user: DBUser, request: HTTPConnection) -> List[str]:
        scopes = ['authenticated']

        if user.activated:
            scopes.append('activated')

        if not user.restricted:
            scopes.append('unrestricted')

        if not user.silence_end:
            scopes.append('unsilenced')

        for group in await self.fetch_user_groups(user.id, request):
            scopes.append(group.lower())

        return scopes

    def parse_authorization(self, authorization: str) -> dict[str, str]:
        if ' ' not in authorization:
            return {'scheme': '', 'data': ''}

        scheme, data = authorization.split(' ', 1)
        return {'scheme': scheme.lower(), 'data': data}

api.add_middleware(AuthenticationMiddleware, backend=AuthBackend())
