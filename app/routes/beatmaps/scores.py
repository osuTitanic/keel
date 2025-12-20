
from fastapi import APIRouter, HTTPException, Request, Query
from contextlib import suppress

from app.common.config import config_instance as config
from app.common.database import scores, beatmaps
from app.common.constants import GameMode
from app.models import *

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Beatmap not found"},
        400: {"model": ErrorResponse, "description": "Invalid game mode"}
    }
)

user_responses = {
    404: {"model": ErrorResponse, "description": "User not found"},
}

@router.get("/{id}/scores", response_model=ScoreCollectionResponseWithoutBeatmap)
def get_beatmap_scores(
    request: Request, id: int,
    offset: int = Query(0, ge=0),
    mods: str | None = Query(None),
    mode: GameMode | None = Query(None)
) -> ScoreCollectionResponseWithoutBeatmap:
    if not (beatmap := beatmaps.fetch_by_id(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    # Set to default mode from beatmap if not provided
    default_mode = GameMode(beatmap.mode)
    mode_enum = mode or default_mode

    if (resolved_mods := resolve_mods_from_string(mods)) is not None:
        top_scores = scores.fetch_range_scores_mods(
            id, mode_enum.value, resolved_mods.value,
            offset=offset, limit=config.SCORE_RESPONSE_LIMIT,
            session=request.state.db
        )
        score_count = scores.fetch_count_beatmap(
            beatmap.id,
            mode_enum.value, resolved_mods.value,
            session=request.state.db
        )

    else:
        top_scores = scores.fetch_range_scores(
            id, mode_enum.value,
            offset=offset,
            limit=config.SCORE_RESPONSE_LIMIT,
            session=request.state.db
        )
        score_count = scores.fetch_count_beatmap(
            beatmap.id,
            mode_enum.value,
            session=request.state.db
        )

    return ScoreCollectionResponseWithoutBeatmap(
        total=score_count,
        scores=[
            ScoreModelWithoutBeatmap.model_validate(score, from_attributes=True)
            for score in top_scores
        ]
    )

@router.get("/{beatmap_id}/scores/users/{user_id}", response_model=ScoreCollectionResponseWithoutBeatmap, responses=user_responses)
def get_beatmap_user_scores(
    request: Request,
    beatmap_id: int,
    user_id: int,
    mode: GameMode | None = Query(None)
) -> ScoreCollectionResponseWithoutBeatmap:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    # Set to default mode from beatmap if not provided
    default_mode = GameMode(beatmap.mode)
    mode_enum = mode or default_mode

    user_scores = scores.fetch_best_by_beatmap(
        user_id, beatmap_id,
        mode_enum.value,
        session=request.state.db
    )

    return ScoreCollectionResponseWithoutBeatmap(
        total=len(user_scores),
        scores=[
            ScoreModelWithoutBeatmap.model_validate(score, from_attributes=True)
            for score in user_scores
        ]
    )

@router.get("/{beatmap_id}/scores/users/{user_id}/best", response_model=ScoreModel, responses=user_responses)
def get_beatmap_user_personal_best(
    request: Request,
    beatmap_id: int,
    user_id: int,
    mode: GameMode | None = Query(None),
    mods: str | None = Query(None)
) -> ScoreModel:
    if not (beatmap := beatmaps.fetch_by_id(beatmap_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmap.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    # Set to default mode from beatmap if not provided
    default_mode = GameMode(beatmap.mode)
    mode_enum = mode or default_mode
    resolved_mods = resolve_mods_from_string(mods)

    score = scores.fetch_personal_best_score(
        beatmap_id, user_id,
        mode_enum.value,
        mods=resolved_mods,
        session=request.state.db
    )

    if not score:
        raise HTTPException(
            status_code=404,
            detail="The requested user score could not be found"
        )

    return ScoreModel.model_validate(score, from_attributes=True)

def resolve_mods_from_string(mods: str) -> Mods | None:
    if not mods:
        return None

    with suppress(Exception):
        if mods.isdigit():
            return Mods(int(mods))
        else:
            return Mods.from_string(mods)

    return None
