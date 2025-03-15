
from fastapi.middleware.cors import CORSMiddleware
from config import DOMAIN_NAME
from app import api

origins = [
    f"http://localhost:8080",
    f"http://127.0.0.1:8080",
    f"http://api.{DOMAIN_NAME}",
    f"https://api.{DOMAIN_NAME}",
    f"http://osu.{DOMAIN_NAME}",
    f"https://osu.{DOMAIN_NAME}",
    f"http://{DOMAIN_NAME}",
    f"https://{DOMAIN_NAME}",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
