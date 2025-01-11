
from app.routes import router as BaseRouter
from fastapi import FastAPI

import logging
import config

logging.basicConfig(
    format='[%(asctime)s] - <%(name)s> %(levelname)s: %(message)s',
    level=logging.DEBUG if config.DEBUG else logging.INFO,
)

api = FastAPI(
    title='titanic-api',
    description='Titanic! API',
    debug=config.DEBUG
)
api.include_router(BaseRouter)
