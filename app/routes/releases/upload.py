
from fastapi import HTTPException, APIRouter, Request, Query, Body
from app.models import OsuReleaseUploadRequest, OsuReleaseModel
from app.common.database import releases
from app.utils import requires

router = APIRouter()

@router.post("/official", response_model=OsuReleaseModel)
@requires("clients.upload")
def create_release(
    request: Request,
    release: OsuReleaseUploadRequest = Body(...)
) -> OsuReleaseModel:
    file_ids = [
        releases.fetch_file_id_from_version(file_version, request.state.db)
        for file_version in release.files
    ]

    if any(file_id is None for file_id in file_ids):
        raise HTTPException(status_code=400, detail="One or more file versions were not found.")

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
