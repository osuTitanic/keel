
from fastapi import APIRouter, Request, Query
from datetime import datetime
from typing import List

from app.common.database import changelog
from app.models import OsuChangelogModel

router = APIRouter()

# TODO: Parse this from configuration
client_cutoff = datetime(2015, 12, 30)
min_date = datetime(2007, 1, 1)

@router.get("/changelog", response_model=List[OsuChangelogModel])
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
