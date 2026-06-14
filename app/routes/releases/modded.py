
from fastapi import HTTPException, APIRouter, Request, Query, Body
from typing import List

from app.models import ModdedReleaseModel, ModdedReleaseUploadRequest, ModdedReleaseUpdatePath, ModdedReleaseEntryModel
from app.common.database import releases
from app.utils import requires

router = APIRouter()

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

@router.get("/modded/{identifier}/entries", response_model=List[ModdedReleaseEntryModel])
def get_modded_release_entries(
    request: Request,
    identifier: str,
    version: str | None = Query(None),
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
            version=version,
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

@router.get("/modded/{identifier}/update", response_model=ModdedReleaseUpdatePath)
def get_modded_release_update_path(
    request: Request,
    identifier: str,
    # Any one of these has to be provided to identify the source release
    checksum: str | None = Query(None),
    version: str | None = Query(None),
    stream: str | None = Query(None)
) -> ModdedReleaseUpdatePath:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(
            status_code=404,
            detail="The requested release was not found"
        )

    source_release = resolve_source_release(
        release_object.name, checksum,
        version, stream, request
    )
    if not source_release:
        raise HTTPException(
            status_code=404,
            detail="Source release not found"
        )

    target_release = releases.fetch_modded_entry_latest(
        release_object.name,
        source_release.stream,
        request.state.db
    )
    if not target_release:
        raise HTTPException(
            status_code=404,
            detail="Target release not found"
        )

    if source_release.id == target_release.id:
        return ModdedReleaseUpdatePath(
            client=ModdedReleaseModel.model_validate(release_object, from_attributes=True),
            source_release=ModdedReleaseEntryModel.model_validate(source_release, from_attributes=True),
            target_release=None,
            stream=source_release.stream,
            path=[]
        )

    path = releases.fetch_modded_entries_between(
        release_object.name,
        source_release.id,
        target_release.id,
        source_release.stream,
        request.state.db
    )

    return ModdedReleaseUpdatePath(
        client=ModdedReleaseModel.model_validate(release_object, from_attributes=True),
        source_release=ModdedReleaseEntryModel.model_validate(source_release, from_attributes=True),
        target_release=ModdedReleaseEntryModel.model_validate(target_release, from_attributes=True),
        stream=source_release.stream,
        path=[
            ModdedReleaseEntryModel.model_validate(entry, from_attributes=True)
            for entry in path
        ]
    )

def resolve_source_release(
    mod_name: str,
    checksum: str | None,
    version: str | None,
    stream: str | None,
    request: Request
) -> releases.DBModdedReleaseEntries | None:
    if checksum:
        entry = releases.fetch_modded_entry_by_checksum(
            mod_name,
            checksum,
            request.state.db
        )
        if entry:
            return entry

    if version and stream:
        entry = releases.fetch_modded_entry_by_version(
            mod_name,
            version,
            stream,
            request.state.db
        )
        if entry:
            return entry

    return None
