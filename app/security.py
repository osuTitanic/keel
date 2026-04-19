
from app.common.config import config_instance as config
from app.common.constants import TokenSource
from app.common.database import DBUser
from fastapi import Header, Depends
from hashlib import md5
from app import utils
from redis.asyncio import Redis as RedisAsync

import bcrypt
import json
import time
import jwt

WEBSITE_SESSION_COOKIE_NAME = "titanic_session"

def generate_token(user: DBUser, expiry: int, source=TokenSource.Web) -> str:
    return jwt.encode(
        {
            'id': user.id,
            'name': user.name,
            'exp': expiry,
            'source': source.value
        },
        config.FRONTEND_SECRET_KEY,
        algorithm='HS256'
    )

def validate_token(token: str) -> dict | None:
    try:
        data = jwt.decode(
            token,
            config.FRONTEND_SECRET_KEY,
            algorithms=['HS256']
        )
    except jwt.PyJWTError:
        return

    # Check if the token is expired
    if time.time() > data['exp']:
        return

    return data

async def validate_website_session(session_id: str, redis: RedisAsync) -> dict | None:
    if not session_id or redis is None:
        return None

    payload = await redis.get(f"authentication:website:{session_id}")

    if not payload:
        return None

    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return None

    if time.time() > data["expires_at"]:
        return None

    return data

def password_authentication(password: str, bcrypt_hash: str) -> bool:
    return md5_authentication(
        md5(password.encode()).hexdigest(),
        bcrypt_hash
    )

def md5_authentication(md5: str, bcrypt_hash: str) -> bool:
    return bcrypt.checkpw(
        md5.encode(),
        bcrypt_hash.encode()
    )

async def md5_authentication_async(md5: str, bcrypt: str) -> bool:
    return await utils.run_async(
        md5_authentication,
        md5, bcrypt
    )

async def password_authentication_async(password: str, bcrypt: str) -> bool:
    return await md5_authentication_async(
        md5(password.encode()).hexdigest(),
        bcrypt
    )

def require_login_function(authorization: str = Header(None, alias="Authorization")):
    return authorization

require_login = Depends(require_login_function)
