
from app.routes.media.api import BitviewAPI
from app.models import BitviewVideoModel

from fastapi import HTTPException, APIRouter, Request
from typing import List

import config
import json

bitview = BitviewAPI(
    config.BITVIEW_API_ENDPOINT,
    config.BITVIEW_USERNAME,
    config.BITVIEW_CLOUDFLARE_SOLVER
)
router = APIRouter()

@router.get("/bitview")
def bitview_channel_playlist(request: Request) -> List[BitviewVideoModel]:
    if not config.BITVIEW_ENABLED:
        raise HTTPException(404, "Bitview integration is disabled.")

    return bitview.fetch_videos().values()
