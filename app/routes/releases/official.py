
from fastapi import HTTPException, APIRouter, Request, Query, Body
from datetime import datetime
from typing import List

from app.models import OsuReleaseUploadRequest, OsuChangelogModel, OsuReleaseModel
from app.common.database import releases, changelog
from app.utils import requires

router = APIRouter()

# TODO: Parse this from configuration
client_cutoff = datetime(2015, 12, 30)
min_date = datetime(2007, 1, 1)

@router.get("/official", response_model=List[OsuReleaseModel])
def get_official_releases(
    request: Request,
    stream: str | None = Query(None),
    before: datetime | None = Query(None),
    after: datetime | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[OsuReleaseModel]:
    entries = releases.fetch_official_range(
        limit=limit,
        offset=offset,
        stream=stream,
        before=before,
        after=after,
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

@router.get("/official/changelog", response_model=List[OsuChangelogModel])
def get_osu_changelog(
    request: Request,
    start: datetime = Query(client_cutoff, ge=min_date),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> List[OsuChangelogModel]:
    # Ensure we have no timezone set
    start = start.replace(tzinfo=None)

    # Pretend that its still 2015™
    if start > client_cutoff:
        start = client_cutoff

    return [
        OsuChangelogModel.model_validate(
            entry,
            from_attributes=True
        )
        for entry in changelog.fetch_range_desc(
            start_date=start,
            limit=limit, offset=offset,
            session=request.state.db
        )
    ]
