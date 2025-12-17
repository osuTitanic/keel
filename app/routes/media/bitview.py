
from app.common.config import config_instance as config
from app.routes.media.api import BitviewAPI
from app.models import BitviewVideoModel

from fastapi import BackgroundTasks, HTTPException, APIRouter, Request
from typing import List

bitview = BitviewAPI(
    config.BITVIEW_API_ENDPOINT,
    config.BITVIEW_USERNAME,
    config.BITVIEW_CLOUDFLARE_SOLVER
)
router = APIRouter()

@router.get("/bitview")
def bitview_channel_playlist(request: Request, background_tasks: BackgroundTasks) -> List[BitviewVideoModel]:
    if not config.BITVIEW_ENABLED:
        raise HTTPException(404, "Bitview integration is disabled.")

    return bitview.fetch_videos(background_tasks).values()
