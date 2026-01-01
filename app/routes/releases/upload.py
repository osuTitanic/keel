
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

@router.post("/modded/{identifier}", response_model=ModdedReleaseEntryModel)
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

@router.delete("/modded/{identifier}/{checksum}")
@requires("releases.modded.delete")
def delete_modded_release(
    request: Request,
    identifier: str,
    checksum: str
) -> dict:
    release_object = releases.fetch_modded(
        identifier=identifier,
        session=request.state.db
    )

    if not release_object:
        raise HTTPException(status_code=404, detail="The requested release was not found")

    if request.user.id != release_object.creator_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete entries for this release")

    entry = releases.fetch_modded_entry_by_checksum(
        mod_name=release_object.name,
        checksum=checksum,
        session=request.state.db
    )

    if not entry:
        raise HTTPException(status_code=404, detail="The requested release entry was not found")

    releases.delete_modded_entry(
        entry_id=entry.id,
        session=request.state.db
    )
    return {}
