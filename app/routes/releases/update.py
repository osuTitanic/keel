
from fastapi import HTTPException, APIRouter, Request, Query, Body
from app.common.database import releases, DBModdedRelease
from app.models.releases import *
from app.utils import requires

router = APIRouter()

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
        raise HTTPException(
            status_code=404,
            detail="Already on the latest version"
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
        stream=source_release.stream,
        source_release=ModdedReleaseEntryModel.model_validate(source_release, from_attributes=True),
        target_release=ModdedReleaseEntryModel.model_validate(target_release, from_attributes=True),
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
