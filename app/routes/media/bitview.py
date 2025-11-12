
from app.models import BitviewVideoListing, BitviewVideoModel
from fastapi import HTTPException, APIRouter, Request
from typing import List

import config
import json

router = APIRouter()

@router.get("/bitview")
def bitview_channel_playlist(request: Request) -> List[BitviewVideoModel]:
    if not config.BITVIEW_ENABLED:
        raise HTTPException(404, "Bitview integration is disabled.")

    return fetch_bitview_video_listing(request, config.BITVIEW_USERNAME).values()

def fetch_bitview_video_listing(request: Request, username: str) -> BitviewVideoListing:
    response = request.state.requests.get(
        config.BITVIEW_API_ENDPOINT,
        params={"username": username}
    )

    if response.status_code != 200:
        # Fallback to backup response
        return BACKUP_RESPONSE

    return response.json()

BACKUP_RESPONSE = {
    "1": {
        "url": "DrY8GIkr",
        "file_url": "dZKoveKbLwmPjmqyt3xW",
        "title": "ame | Step on Stage FC!",
        "uploaded_on": "2025-08-19 18:17:12"
    },
    "2": {
        "url": "ROt56Bpb",
        "file_url": "UeuUdi8k4p36b2pG8yJz",
        "title": "nano | Necro Fantasia +NC FC",
        "uploaded_on": "2025-08-10 01:11:47"
    },
    "3": {
        "url": "t8Zi9nBU",
        "file_url": "JATcP1oiKAjmk7SZohNj",
        "title": "EZChamp | Made of Fire +DT FC",
        "uploaded_on": "2025-06-10 17:43:15"
    },
    "4": {
        "url": "ymBBFzFn",
        "file_url": "v65K2jY4Im152n20esOT",
        "title": "EZChamp | FREEDOM DiVE +HR FC",
        "uploaded_on": "2025-06-10 17:26:17"
    }
}
