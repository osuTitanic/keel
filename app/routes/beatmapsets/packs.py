
from app.models import ErrorResponse, BeatmapPackModel, BeatmapPackWithEntriesModel
from app.common.database import packs

from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import RedirectResponse
from typing import List

router = APIRouter()

pack_responses = {
    404: {'description': 'Beatmap pack not found', 'model': ErrorResponse},
    301: {'description': 'Redirect to the correct category'}
}

@router.get("/packs", response_model=List[BeatmapPackModel])
def get_beatmap_packs(request: Request):
    return [
        BeatmapPackModel.model_validate(pack, from_attributes=True)
        for pack in packs.fetch_all(request.state.db)
    ]

@router.get("/packs/{category}", response_model=List[BeatmapPackModel])
def get_beatmap_packs_by_category(request: Request, category: str):
    return [
        BeatmapPackModel.model_validate(pack, from_attributes=True)
        for pack in packs.fetch_by_category(category, request.state.db)
    ]

@router.get("/packs/{category}/{pack_id}", response_model=BeatmapPackWithEntriesModel, responses=pack_responses)
def get_beatmap_pack(request: Request, category: str, pack_id: int):
    if not (pack := packs.fetch_one(pack_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail='The requested beatmap pack could not be found'
        )

    if pack.category != category:
        return RedirectResponse(
            url=f'/beatmapsets/packs/{pack.category}/{pack.id}',
            status_code=301
        )

    return BeatmapPackWithEntriesModel.model_validate(pack, from_attributes=True)
