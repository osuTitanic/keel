
from app.common.database.objects import DBUser
from app.common.database import users, stats
from app.common.cache import leaderboards
from app import utils
from app.models import (
    UserModelWithStats,
    RankingEntryModel,
    RankingStatsModel,
    OrderType,
    ModeAlias
)

from fastapi import Request, APIRouter, Query
from sqlalchemy.orm import Session
from typing import List

import app.session

router = APIRouter()

@router.get("/{order}/{mode}", response_model=List[RankingEntryModel])
def get_rankings(
    request: Request,
    order: OrderType,
    mode: ModeAlias,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50),
    country: str | None = Query(None)
) -> List[RankingEntryModel]:
    top_players = leaderboards.top_players(
        mode.integer,
        offset, limit,
        order.value,
        country=(
            country.lower()
            if country is not None else None
        )
    )

    # Fetch user info from database
    user_objects = users.fetch_many(
        tuple([user_id for user_id, score in top_players]),
        DBUser.stats,
        session=request.state.db
    )
    users_by_id = {
        user.id: user
        for user in user_objects
    }

    # Sort players based on redis leaderboard
    sorted_players = [
        users_by_id[user_id]
        for user_id, score in top_players
    ]

    stats_by_user_id = resolve_stats_models(
        sorted_players,
        mode.integer
    )

    return [
        RankingEntryModel(
            index=index + offset + 1,
            score=score,
            user=UserModelWithStats.model_validate(sorted_players[index], from_attributes=True),
            stats=stats_by_user_id[sorted_players[index].id]
        )
        for index, (user_id, score) in enumerate(top_players)
    ]

def resolve_stats_models(users: List[DBUser], mode: int) -> dict[int, RankingStatsModel]:
    if not users:
        return {}

    rank_keys = (
        ('global_rank', lambda user: f'bancho:performance:{mode}'),
        ('country_rank', lambda user: f'bancho:performance:{mode}:{user.country.lower()}'),
        ('score_rank', lambda user: f'bancho:rscore:{mode}'),
        ('score_rank_country', lambda user: f'bancho:rscore:{mode}:{user.country.lower()}'),
        ('total_score_rank', lambda user: f'bancho:tscore:{mode}'),
        ('total_score_rank_country', lambda user: f'bancho:tscore:{mode}:{user.country.lower()}'),
        ('ppv1_rank', lambda user: f'bancho:ppv1:{mode}'),
        ('ppv1_rank_country', lambda user: f'bancho:ppv1:{mode}:{user.country.lower()}')
    )
    requests = []

    with app.session.redis.pipeline() as pipe:
        for user in users:
            for field, key_factory in rank_keys:
                pipe.zrevrank(key_factory(user), user.id)
                requests.append((user.id, field))

        results = pipe.execute()

    rank_values = {
        user.id: {}
        for user in users
    }

    for (user_id, field), rank in zip(requests, results):
        rank_values[user_id][field] = (
            rank + 1 if rank is not None else 0
        )

    return {
        user_id: RankingStatsModel(**values)
        for user_id, values in rank_values.items()
    }
