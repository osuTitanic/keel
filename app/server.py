
from app.routes import router as BaseRouter
from fastapi import FastAPI

import logging
import config

logging.basicConfig(
    format='[%(asctime)s] - <%(name)s> %(levelname)s: %(message)s',
    level=logging.DEBUG if config.DEBUG else logging.INFO,
)

description = """\
Welcome to the documentation for the Titanic! API.  
This service lets you access & interact with (almost) everything Titanic! has to offer.

Note that this documentation may contain parts that are incorrect and contain errors.  
Don't be afraid to report them on our GitHub repository.
"""

api = FastAPI(
    title='Titanic! API',
    description=description,
    version=config.VERSION,
    debug=config.DEBUG,
    redoc_url="/docs",
    docs_url=None,
    contact={
        "name": "Titanic",
        "url": "https://osu.titanic.sh",
        "email": "support@titanic.sh"
    },
    servers=[
        {
            "url": f"https://api.{config.DOMAIN_NAME}",
            "description": "Production server"
        }
    ]
)
api.include_router(BaseRouter)

if config.DEBUG:
    # Add development server
    api.servers.append({
        "url": f"http://localhost:{config.API_PORT}",
        "description": "Local server"
    })
