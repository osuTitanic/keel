
from app.common.database.repositories import beatmapsets
from app.models import SearchRequest, BeatmapsetModel
from fastapi import APIRouter, Request
from typing import List

router = APIRouter()

@router.post("/search", response_model=List[BeatmapsetModel])
def search_beatmapsets(request: Request, query: SearchRequest):
    user_id = (
        request.user.id
        if request.user.is_authenticated else None
    )

    results = beatmapsets.search_extended(
        query.query,
        query.genre,
        query.language,
        query.played,
        query.unplayed,
        query.cleared,
        query.uncleared,
        user_id,
        query.mode,
        query.order,
        query.category,
        query.sort,
        query.storyboard,
        query.video,
        query.titanic,
        offset=query.page * 50,
        limit=50,
        session=request.state.db
    )

    return [
        BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
        for beatmapset in results
    ]
