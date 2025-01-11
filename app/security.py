
from __future__ import annotations
from app.common.database import DBUser
from hashlib import md5

import asyncio
import config
import bcrypt
import time
import jwt

def generate_token(user: DBUser, expiry: int) -> str:
    return jwt.encode(
        {
            'id': user.id,
            'name': user.name,
            'exp': expiry,
        },
        config.FRONTEND_SECRET_KEY,
        algorithm='HS256'
    )

def decode_token(token: str) -> dict | None:
    try:
        data = jwt.decode(
            token,
            config.FRONTEND_SECRET_KEY,
            algorithms=['HS256']
        )
    except jwt.PyJWTError:
        return

    # Check if the token is expired
    if data['exp'] < round(time.time()):
        return

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
    return await asyncio.get_event_loop().run_in_executor(
        None, md5_authentication,
        md5, bcrypt
    )

async def password_authentication_async(password: str, bcrypt: str) -> bool:
    return await md5_authentication_async(
        md5(password.encode()).hexdigest(),
        bcrypt
    )
