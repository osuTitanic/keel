
from fastapi.middleware.cors import CORSMiddleware
from app.common.config import config_instance as config
from app import api

origins = [
    f"http://localhost",
    f"http://osu.localhost",
    f"http://localhost:8080",
    f"http://127.0.0.1:8080",
    f"http://api.{config.DOMAIN_NAME}",
    f"https://api.{config.DOMAIN_NAME}",
    f"http://osu.{config.DOMAIN_NAME}",
    f"https://osu.{config.DOMAIN_NAME}",
    f"http://{config.DOMAIN_NAME}",
    f"https://{config.DOMAIN_NAME}",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
