
from fastapi import HTTPException, APIRouter, Request, Query, Body
from app.common.database import releases
from app.models.releases import *
from app.utils import requires

router = APIRouter()

@router.post("/official", response_model=OsuReleaseModel)
@requires("releases.upload")
def create_official_release(
    request: Request,
    release: OsuReleaseUploadRequest = Body(...)
) -> OsuReleaseModel:
    file_ids = [
        releases.fetch_file_id_from_version(file_version, request.state.db)
        for file_version in release.files
    ]

    if any(file_id is None for file_id in file_ids):
        raise HTTPException(status_code=400, detail="One or more file versions were not found")

    release_object = releases.create_official(
        version=release.version,
        subversion=release.subversion,
        created_at=release.created_at,
        stream=release.stream,
        session=request.state.db
    )
    release_files = {release_object.id: []}

    for file_id in file_ids:
        file = releases.create_official_file_entry(
            release_id=release_object.id,
            file_id=file_id,
            session=request.state.db
        )
        release_files[release_object.id].append(file)

    return OsuReleaseModel.model_validate(
        release_object,
        context=release_files,
        from_attributes=True
    )

@router.delete("/official/{release_id}")
@requires("releases.delete")
def delete_official_release(
    request: Request,
    release_id: int
) -> dict:
    release_object = releases.fetch_official_by_id(
        release_id=release_id,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    releases.delete_official(
        release_id=release_id,
        session=request.state.db
    )
    return {}

@router.get("/modded/{identifier}/entries", response_model=List[ModdedReleaseEntryModel])
def get_modded_release_entries(
    request: Request,
    identifier: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[ModdedReleaseEntryModel]:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    return [
        ModdedReleaseEntryModel.model_validate(
            entry,
            from_attributes=True
        )
        for entry in releases.fetch_modded_entries(
            mod_name=release_object.name,
            limit=limit, offset=offset,
            session=request.state.db
        )
    ]

@router.post("/modded/{identifier}/entries", response_model=ModdedReleaseEntryModel)
@requires("releases.modded.upload")
def upload_modded_release(
    request: Request,
    identifier: str,
    release: ModdedReleaseUploadRequest = Body(...)
) -> ModdedReleaseEntryModel:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    if request.user.id != release_object.creator_id:
        raise HTTPException(status_code=403, detail="You do not have permission to upload entries for this release")

    release_object = releases.create_modded_entry(
        mod_name=release_object.name,
        version=release.version,
        stream=release.stream,
        checksum=release.checksum,
        download_url=release.download_url,
        update_url=release.update_url,
        post_id=release.post_id,
        session=request.state.db
    )
    return ModdedReleaseEntryModel.model_validate(
        release_object,
        from_attributes=True
    )

@router.delete("/modded/{identifier}/entries/{id}")
@requires("releases.modded.delete")
def delete_modded_release(
    request: Request,
    identifier: str,
    id: int
) -> dict:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    if request.user.id != release_object.creator_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete entries for this release")

    entry = releases.fetch_modded_entry_by_id(
        mod_name=release_object.name,
        entry_id=id,
        session=request.state.db
    )

    if not entry:
        raise HTTPException(status_code=404, detail="The requested release entry was not found")

    releases.delete_modded_entry(
        entry_id=entry.id,
        session=request.state.db
    )
    return {}

@router.get("/modded/{identifier}/entries/{id}", response_model=ModdedReleaseEntryModel)
def get_modded_release_entry(
    request: Request,
    identifier: str,
    id: int
) -> ModdedReleaseEntryModel:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    entry_object = releases.fetch_modded_entry_by_id(
        mod_name=release_object.name,
        entry_id=id,
        session=request.state.db
    )

    if not entry_object:
        raise HTTPException(status_code=404, detail="The requested release entry was not found")

    return ModdedReleaseEntryModel.model_validate(
        entry_object,
        from_attributes=True
    )

@router.patch("/modded/{identifier}/entries/{id}", response_model=ModdedReleaseEntryModel)
@requires("releases.modded.upload")
def update_modded_release_entry(
    request: Request,
    identifier: str,
    id: int,
    update_data: ModdedReleaseUploadRequest
) -> ModdedReleaseEntryModel:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    if request.user.id != release_object.creator_id:
        raise HTTPException(status_code=403, detail="You do not have permission to upload entries for this release")

    entry_object = releases.fetch_modded_entry_by_id(
        mod_name=release_object.name,
        entry_id=id,
        session=request.state.db
    )

    if not entry_object:
        raise HTTPException(status_code=404, detail="The requested release entry was not found")

    releases.update_modded_entry(
        entry_id=id,
        updates=update_data.model_dump(exclude_unset=True),
        session=request.state.db
    )
    request.state.db.refresh(entry_object)

    return ModdedReleaseEntryModel.model_validate(
        entry_object,
        from_attributes=True
    )
