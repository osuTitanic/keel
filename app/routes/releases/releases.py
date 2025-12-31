
from fastapi import APIRouter, Request
from typing import List

from app.models import TitanicReleaseModel, ModdedReleaseModel
from app.common.database import releases

router = APIRouter()

@router.get("/", response_model=List[TitanicReleaseModel])
def get_titanic_releases(request: Request) -> List[TitanicReleaseModel]:
    return [
        TitanicReleaseModel.model_validate(client, from_attributes=True)
        for client in releases.fetch_all(request.state.db)
    ]

@router.get("/modded", response_model=List[ModdedReleaseModel])
def get_modded_releases(request: Request) -> List[ModdedReleaseModel]:
    return [
        ModdedReleaseModel.model_validate(client, from_attributes=True)
        for client in releases.fetch_modded_all(request.state.db)
    ]
