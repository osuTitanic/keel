
from .common.cache.events import EventQueue
from .common.database import Postgres
from .common.storage import Storage

from redis.asyncio import Redis as RedisAsync
from requests import Session
from redis import Redis

import logging
import config
import time

database = Postgres(
    config.POSTGRES_USER,
    config.POSTGRES_PASSWORD,
    config.POSTGRES_HOST,
    config.POSTGRES_PORT
)

redis = Redis(
    config.REDIS_HOST,
    config.REDIS_PORT
)

redis_async = RedisAsync(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True
)

events = EventQueue(
    name='bancho:events',
    connection=redis
)

logger = logging.getLogger('titanic')
startup_time = time.time()

storage = Storage()
requests = Session()
requests.headers = {
    'User-Agent': f'osuTitanic ({config.DOMAIN_NAME})'
}
