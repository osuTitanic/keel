
from app.common.config import config_instance as config
from app.common.database.objects import DBUser
from app.common.constants import TokenSource
from app import utils

from redis.asyncio import Redis as RedisAsync
from redis import Redis
from fastapi import Header, Depends
from hashlib import md5

import asyncio
import secrets
import bcrypt
import json
import time
import jwt

WEBSITE_SESSION_COOKIE_NAME = "titanic_session"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_ACCESS = "access"

def session_key(token_id: str) -> str:
    return f"authentication:session:{token_id}"

def generate_token(
    user: "DBUser",
    expiry: int,
    source=TokenSource.Web,
    token_type: str = TOKEN_TYPE_ACCESS,
    issued_at: int | None = None,
    token_id: str | None = None,
) -> str:
    issued_at = issued_at or int(time.time())
    token_id = token_id or secrets.token_hex(16)

    return jwt.encode(
        {
            'id': user.id,
            'name': user.name,
            'exp': expiry,
            'iat': issued_at,
            'source': int(source),
            'type': token_type,
            'jti': token_id,
        },
        config.FRONTEND_SECRET_KEY,
        algorithm='HS256'
    )

def validate_token(token: str, token_type: str | None = None) -> dict | None:
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

    if data.get('type') not in (TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH):
        return None

    if token_type is not None and data['type'] != token_type:
        return None

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

def session_from_claims(claims: dict | None) -> dict | None:
    if not claims:
        return None

    if claims['type'] not in (TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH):
        return None

    return {
        'token_id': claims['jti'],
        'user_id': claims['id'],
        'source': claims['source'],
        'type': claims['type'],
        'issued_at': claims['iat'],
        'expiry': claims['exp'],
    }

def issue_api_token_pair(user: "DBUser", redis: Redis, source=TokenSource.Api, now: int | None = None) -> dict:
    now = int(time.time()) if now is None else now
    expiry = now + config.FRONTEND_TOKEN_EXPIRY
    expiry_refresh = now + config.FRONTEND_REFRESH_EXPIRY

    access_token = generate_token(
        user,
        expiry,
        source,
        TOKEN_TYPE_ACCESS,
        issued_at=now
    )
    refresh_token = generate_token(
        user,
        expiry_refresh,
        source,
        TOKEN_TYPE_REFRESH,
        issued_at=now
    )

    refresh_claims = validate_token(
        refresh_token,
        TOKEN_TYPE_REFRESH
    )
    if not refresh_claims or not upsert_api_session(refresh_claims, redis, now):
        raise RuntimeError("Failed to persist refresh session")

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expiry,
        'token_type': 'Bearer'
    }

def upsert_api_session(claims: dict | None, redis: Redis, now: int | None = None) -> dict | None:
    session = session_from_claims(claims)
    if not session:
        return None

    now = int(time.time()) if now is None else now
    ttl = session['expiry'] - now

    if ttl <= 0:
        return None

    redis.setex(
        session_key(session['token_id']),
        ttl,
        json.dumps(session)
    )
    return session

def validate_api_session(claims: dict | None, redis: Redis, now: int | None = None) -> bool:
    session = session_from_claims(claims)
    if not session:
        return False

    now = now or int(time.time())
    if now > session['expiry']:
        return False

    payload = redis.get(session_key(session['token_id']))
    if not payload:
        return False

    if isinstance(payload, bytes):
        payload = payload.decode()

    try:
        stored = json.loads(payload)
    except (TypeError, ValueError):
        return False

    if stored != session:
        return False

    return now <= stored['expiry']

async def validate_api_session_async(claims: dict | None, redis: RedisAsync, now: int | None = None) -> bool:
    session = session_from_claims(claims)
    if not session:
        return False

    now = now or int(time.time())
    if now > session['expiry']:
        return False

    payload = await redis.get(session_key(session['token_id']))
    if not payload:
        return False

    try:
        stored = json.loads(payload)
    except (TypeError, ValueError):
        return False

    if stored != session:
        return False

    return now <= stored['expiry']

def delete_api_session(claims: dict | None, redis: Redis) -> bool:
    session = session_from_claims(claims)
    if not session:
        return False

    return bool(redis.delete(session_key(session['token_id'])))

def validate_refresh_token(token: str, redis: Redis, now: int | None = None) -> dict | None:
    claims = validate_token(token)
    if not claims:
        return None

    if claims['type'] != TOKEN_TYPE_REFRESH:
        return None

    if validate_api_session(claims, redis, now):
        return claims

    return None

async def validate_api_token(token: str, redis: RedisAsync, now: int | None = None) -> dict | None:
    claims = validate_token(token)
    if not claims:
        return None

    # Refresh tokens are only accepted when the redis session entry still matches
    if claims['type'] != TOKEN_TYPE_REFRESH:
        return claims

    if await validate_api_session_async(claims, redis, now):
        return claims

    return None

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
