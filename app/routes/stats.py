
from app.models import ServerStatsModel, BeatmapModeStatsModel
from fastapi import HTTPException, APIRouter, Request
from typing import Tuple, Any

import app.session
import time

router = APIRouter()

@router.get("/stats", response_model=ServerStatsModel)
def server_stats(request: Request):
    response = fetch_server_stats(request)

    if not response:
        raise HTTPException(status_code=500, detail="Failed to fetch server stats")

    return parse_stats_response(response)

def fetch_server_stats(request: Request):
    keys = [
        "bancho:activity:osu",
        "bancho:activity:irc",
        "bancho:activity:mp",
        "bancho:totalusers",
        "bancho:totalscores",
        "bancho:totalbeatmaps",
        "bancho:totalbeatmapsets",
    ]

    for mode in range(4):
        keys.extend([
            f"bancho:totalbeatmaps:{mode}:-2",
            f"bancho:totalbeatmaps:{mode}:-1",
            f"bancho:totalbeatmaps:{mode}:0",
            f"bancho:totalbeatmaps:{mode}:1",
            f"bancho:totalbeatmaps:{mode}:2",
            f"bancho:totalbeatmaps:{mode}:3",
            f"bancho:totalbeatmaps:{mode}:4",
        ])

    # Use pipeline to fetch all values at once
    with request.state.redis.pipeline() as pipe:
        for key in keys:
            pipe.get(key)

        results = pipe.execute()
        return results

def parse_stats_response(response: Tuple[Any]) -> ServerStatsModel:
    response = [int(value) if value is not None else 0 for value in response]
    offset = 7

    stats = ServerStatsModel(
        uptime=round(time.time() - app.session.startup_time),
        online_users=response[0] + response[1],
        online_users_osu=response[0],
        online_users_irc=response[1],
        online_mp_matches=response[2],
        total_users=response[3],
        total_scores=response[4],
        total_beatmaps=response[5],
        total_beatmapsets=response[6],
        beatmap_modes={}
    )

    for mode in range(4):
        stats.beatmap_modes[mode] = BeatmapModeStatsModel(
            mode=mode,
            count_graveyard=response[offset],
            count_wip=response[offset + 1],
            count_pending=response[offset + 2],
            count_ranked=response[offset + 3],
            count_approved=response[offset + 4],
            count_qualified=response[offset + 5],
            count_loved=response[offset + 6]
        )
        offset += 7
        
    return stats
