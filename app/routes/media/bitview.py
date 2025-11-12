
from app.models import BitviewVideoListing, BitviewVideoModel
from app.common.helpers import caching

from fastapi import HTTPException, APIRouter, Request
from typing import List

import config
import json
import app

router = APIRouter()

@router.get("/bitview")
def bitview_channel_playlist(request: Request) -> List[BitviewVideoModel]:
    if not config.BITVIEW_ENABLED:
        raise HTTPException(404, "Bitview integration is disabled.")

    if config.BITVIEW_CLOUDFLARE_SOLVER:
        return fetch_videos_cloudflare(config.BITVIEW_USERNAME).values()

    return fetch_videos(config.BITVIEW_USERNAME).values()

@caching.ttl_cache(ttl=60*5)
def fetch_videos(username: str) -> BitviewVideoListing:
    response = app.session.requests.get(
        config.BITVIEW_API_ENDPOINT,
        params={"username": username}
    )

    if response.status_code != 200:
        raise HTTPException(502, "Failed to fetch Bitview videos.")

    return response.json()

@caching.ttl_cache(ttl=60*30)
def fetch_videos_cloudflare(username: str) -> BitviewVideoListing:
    # NOTE: This requires a FlareSolverr instance to be running
    # https://github.com/FlareSolverr/FlareSolverr
    response = app.session.requests.post(
        config.BITVIEW_CLOUDFLARE_SOLVER,
        json={
            "cmd": "request.get",
            "url": f"{config.BITVIEW_API_ENDPOINT}?username={username}",
            "maxTimeout": 60000
        },
        headers={
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 200:
        raise HTTPException(502, "Failed to bypass Cloudflare protection.")

    data = response.json()
    response_json = data["solution"]["response"]

    # For some reason, this can contain HTML, so we'll try to extract the JSON part
    response_json = response_json[response_json.index('{'):response_json.rindex('}')+1]

    return json.loads(response_json)
