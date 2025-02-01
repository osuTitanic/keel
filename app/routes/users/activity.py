
from app.common.database import activities, users
from app.models import ActivityModel, ModeAlias
from app.common.constants import GameMode

from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import RedirectResponse
from typing import List

router = APIRouter()

@router.get('/{user_id}/activity')
def get_user_activity_by_preferred_mode(
    request: Request,
    user_id: int
) -> RedirectResponse:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user was not found'
        )

    return RedirectResponse(
        f"/users/{user_id}/activity/{GameMode(user.preferred_mode).alias}",
        status_code=302
    )

@router.get('/{user_id}/activity/{mode}', response_model=List[ActivityModel])
def get_user_activity(
    request: Request,
    user_id: int,
    mode: ModeAlias
) -> List[ActivityModel]:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )
    
    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user was not found'
        )

    # TODO: I really need to refactor the way how I store this...
    recent_activity = [
        (
            activity,
            zip(
                activity.activity_links.split('||'),
                activity.activity_args.split('||')
            )
        )
        for activity in activities.fetch_recent(int(user_id), mode.integer, session=request.state.db)
    ]

    return [
        ActivityModel(
            id=activity.id,
            user_id=activity.user_id,
            mode=activity.mode,
            time=activity.time,
            activity=activity.activity_text.format(
                *(
                    f"[{text}]({link})"
                    for link, text in args
                )
            )
        )
        for activity, args in recent_activity
    ]
