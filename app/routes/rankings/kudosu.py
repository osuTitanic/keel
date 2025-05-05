
from app.models import RankingEntryModelWithoutStats, UserModel
from app.common.database.repositories import users
from app.common.database.objects import DBUser
from app.common.cache import leaderboards

from fastapi import Request, APIRouter, Query
from typing import List

router = APIRouter()

@router.get("/kudosu", response_model=List[RankingEntryModelWithoutStats])
def get_kudosu_rankings(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> List[RankingEntryModelWithoutStats]:
    top_players = leaderboards.top_players(
        None,
        offset,
        limit,
        'kudosu'
    )

    # Fetch user info from database
    user_objects = users.fetch_many(
        tuple([user_id for user_id, _ in top_players]),
        DBUser.stats,
        session=request.state.db
    )

    # Sort players based on redis leaderboard
    sorted_players = [
        next(filter(lambda entry: entry.id == user_id, user_objects))
        for user_id, _ in top_players
    ]

    return [
        RankingEntryModelWithoutStats(
            index=index + offset + 1,
            score=score,
            user=UserModel.model_validate(sorted_players[index], from_attributes=True)
        )
        for index, (user_id, score) in enumerate(top_players)
    ]
