
from app.routes import router as BaseRouter
from contextlib import asynccontextmanager
from fastapi.responses import ORJSONResponse
from fastapi import FastAPI
from app import session

import warnings
import logging

logging.basicConfig(
    format='[%(asctime)s] - <%(name)s> %(levelname)s: %(message)s',
    level=logging.DEBUG if session.config.DEBUG else logging.INFO,
)

description = """\
Welcome to the documentation for the Titanic! API.  
This service lets you access & interact with (almost) everything Titanic! has to offer.

Note that this documentation may contain parts that are incorrect and contain errors.  
Don't be afraid to report them on our GitHub repository.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    session.database.engine.dispose()
    session.database.wait_for_connection()
    session.redis.ping()
    session.filters.populate()
    yield
    session.database.engine.dispose()
    session.redis.close()
    await session.redis_async.close()

api = FastAPI(
    title='Titanic! API',
    description=description,
    version='1.0.0', # eternally 1.0.0
    debug=session.config.DEBUG,
    redoc_url="/docs",
    docs_url=None,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    contact={
        "name": "Titanic",
        "url": "https://osu.titanic.sh",
        "email": "support@titanic.sh"
    },
    servers=[
        {
            "url": f"https://api.{session.config.DOMAIN_NAME}",
            "description": "Production server"
        }
    ]
)
api.include_router(BaseRouter)

if session.config.DEBUG:
    # Add development server
    api.servers.append({
        "url": f"http://localhost:{session.config.API_PORT}",
        "description": "Local server"
    })

if not session.config.DEBUG:
    # Ignore pydantic warnings in production
    warnings.filterwarnings(
        "ignore",
        module="pydantic"
    )
