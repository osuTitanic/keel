
from fastapi import HTTPException, APIRouter, Request, Query
from app.models import StatusModel, StatusStatsModel, StatusRankingModel
from app.common.cache import status, leaderboards

router = APIRouter()

@router.get("/{user_id}/status", response_model=StatusModel)
def get_user_status(request: Request, user_id: int) -> StatusModel:
    if not (user := status.get(user_id)):
        raise HTTPException(404, "The requested user could not be found")

    return StatusModel(
        version=status.version(user_id),
        action=user.status.action,
        mode=user.status.mode,
        mods=user.status.mods,
        beatmap_id=user.status.beatmap_id,
        beatmap_checksum=user.status.beatmap_checksum,
        beatmap_text=user.status.text,
        stats=StatusStatsModel.model_validate(user, from_attributes=True),
        rankings=StatusRankingModel(
            global_rank=leaderboards.global_rank(user_id, user.status.mode.value),
            ppv1_rank=leaderboards.ppv1_rank(user_id, user.status.mode.value),
            score_rank=leaderboards.score_rank(user_id, user.status.mode.value),
            total_score_rank=leaderboards.total_score_rank(user_id, user.status.mode.value)
        )
    )
