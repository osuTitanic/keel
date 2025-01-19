
from fastapi import HTTPException, APIRouter, Request, Body
from app.models import BeatmapUpdateRequestModel, BeatmapsetModel, ErrorResponse
from app.common.database import beatmapsets
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "The requested beatmap could not be found"}
    }
)

@router.get("/{id}", response_model=BeatmapsetModel)
def get_beatmapset(request: Request, id: int) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    if beatmapset.status <= -3:
        raise HTTPException(
            status_code=404,
            detail="The requested beatmap could not be found"
        )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)

@router.patch("/{id}", response_model=BeatmapsetModel, dependencies=[require_login])
@requires("bat")
def update_beatmapset_metadata(
    request: Request,
    id: int,
    update: BeatmapUpdateRequestModel = Body(...)
) -> BeatmapsetModel:
    if not (beatmapset := beatmapsets.fetch_one(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    beatmapsets.update(
        beatmapset.id,
        {
            'tags': update.tags,
            'offset': update.offset,
            'genre_id': update.genre.value,
            'language_id': update.language.value,
            'display_title': (
                update.display_title or
                f"[bold:0,size:20]{beatmapset.artist}|[]{beatmapset.title}"
            )
        },
        request.state.db
    )

    request.state.db.refresh(beatmapset)
    request.state.logger.info(
        f'{request.user.name} updated beatmap metadata for "{beatmapset.full_name}".'
    )

    return BeatmapsetModel.model_validate(beatmapset, from_attributes=True)
