
from fastapi import HTTPException, APIRouter, Request
from app.common.database import users, scores
from app.utils import requires
from datetime import datetime

router = APIRouter()

@router.delete("/scores")
@requires("users.moderation.scores")
def wipe_user_scores(
    request: Request,
    user_id: int
) -> dict:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    scores.hide_all(user.id, request.state.db)
    return {}

@router.post("/scores/restore")
@requires("users.moderation.scores")
def restore_user_scores(
    request: Request,
    user_id: int
) -> dict:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    scores.restore_hidden_scores(user.id, request.state.db)
    return {}
