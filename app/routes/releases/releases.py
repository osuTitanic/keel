
from fastapi import HTTPException, APIRouter, Request, Query
from typing import List

from app.models import TitanicReleaseModel, ModdedReleaseModel, OsuReleaseModel
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

@router.get("/modded/{identifier}", response_model=ModdedReleaseModel)
def get_modded_release(
    request: Request,
    identifier: str
) -> ModdedReleaseModel:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    return ModdedReleaseModel.model_validate(
        release_object,
        from_attributes=True
    )

@router.get("/official", response_model=List[OsuReleaseModel])
def get_official_releases(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[OsuReleaseModel]:
    entries = releases.fetch_official_range(
        limit=limit,
        offset=offset,
        session=request.state.db
    )

    release_files = {
        entry.id: releases.fetch_file_entries(
            release_id=entry.id,
            session=request.state.db
        )
        for entry in entries
    }

    return [
        OsuReleaseModel.model_validate(entry, from_attributes=True, context=release_files)
        for entry in entries
    ]

@router.get("/official/{release_id}", response_model=OsuReleaseModel)
def get_official_release(
    request: Request,
    release_id: int
) -> OsuReleaseModel:
    release_object = releases.fetch_official_by_id(
        release_id=release_id,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    release_files = {
        release_object.id: releases.fetch_file_entries(
            release_id=release_object.id,
            session=request.state.db
        )
    }

    return OsuReleaseModel.model_validate(
        release_object,
        context=release_files,
        from_attributes=True
    )
