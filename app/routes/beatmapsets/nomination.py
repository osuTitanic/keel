
from __future__ import annotations
from fastapi import APIRouter, Request
from typing import List

from app.common.database import nominations
from app.models import NominationModel

router = APIRouter()

@router.get('/{set_id}/nominations', response_model=List[NominationModel])
def get_nominations(request: Request, set_id: int):
    return [
        NominationModel.model_validate(nom, from_attributes=True)
        for nom in nominations.fetch_by_beatmapset(set_id, request.state.db)
    ]
