
from .common.helpers.filter import ChatFilter
from .common.cache.events import EventQueue
from .common.database import Postgres
from .common.storage import Storage
from .common.config import Config

from redis.asyncio import Redis as RedisAsync
from requests import Session
from redis import Redis

import logging
import time

config = Config()
database = Postgres(config)
storage = Storage(config)

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

requests = Session()
filters = ChatFilter()
requests.headers = {
    'User-Agent': f'osuTitanic ({config.DOMAIN_NAME})'
}
