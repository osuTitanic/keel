
from fastapi import APIRouter, HTTPException, Request, Query
from app.common.database import scores, beatmaps
from app.common.constants import GameMode
from app.models import *

import config

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
    mode: str = Query(None),
    offset: int = Query(0, ge=0)
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
    default_mode = GameMode(beatmap.mode).alias
    mode = (mode or default_mode).lower()

    if (mode_enum := GameMode.from_alias(mode)) is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid game mode"
        )

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

@router.get("/{beatmap_id}/scores/users/{user_id}", response_model=ScoreModel, responses=user_responses)
def get_beatmap_user_score(
    request: Request,
    beatmap_id: int, user_id: int,
    mode: str | None = Query(None),
    mods: int | None = Query(None, ge=0)
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
    default_mode = GameMode(beatmap.mode).alias
    mode = (mode or default_mode).lower()

    if (mode_enum := GameMode.from_alias(mode)) is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid game mode"
        )

    score = scores.fetch_personal_best_score(
        beatmap_id, user_id,
        mode_enum.value,
        mods=mods,
        session=request.state.db
    )

    if not score:
        raise HTTPException(
            status_code=404,
            detail="The requested user score could not be found"
        )

    return ScoreModel.model_validate(score, from_attributes=True)
