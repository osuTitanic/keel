
from app.common.database.objects import DBUser
from app.common.database import users, stats
from app.common.cache import leaderboards
from app import utils
from app.models import (
    RankingEntryModel,
    RankingStatsModel,
    UserModel,
    OrderType,
    ModeAlias
)

from fastapi import Request, APIRouter, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.get('/{order}/{mode}', response_model=List[RankingEntryModel])
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
        tuple([user_id for user_id, _ in top_players]),
        DBUser.stats,
        session=request.state.db
    )

    # Sort players based on redis leaderboard
    sorted_players = [
        next(filter(lambda entry: entry.id == user_id, user_objects))
        for user_id, _ in top_players
    ]

    # Ensure every player has their rank
    # synced with the database
    ensure_synced_ranks(
        sorted_players,
        request.state.db
    )

    return [
        RankingEntryModel(
            index=index + offset + 1,
            score=score,
            user=UserModel.model_validate(sorted_players[index], from_attributes=True),
            stats=resolve_stats_model(sorted_players[index], mode.integer)
        )
        for index, (user_id, score) in enumerate(top_players)
    ]

def resolve_stats_model(user: DBUser, mode: int) -> RankingStatsModel:
    return RankingStatsModel(
        global_rank=leaderboards.global_rank(user.id, mode),
        country_rank=leaderboards.country_rank(user.id, mode, user.country),
        score_rank=leaderboards.score_rank(user.id, mode),
        score_rank_country=leaderboards.score_rank_country(user.id, mode, user.country),
        total_score_rank=leaderboards.total_score_rank(user.id, mode),
        total_score_rank_country=leaderboards.total_score_rank_country(user.id, mode, user.country),
        ppv1_rank=leaderboards.ppv1_rank(user.id, mode),
        ppv1_rank_country=leaderboards.ppv1_country_rank(user.id, mode, user.country),
    )

def ensure_synced_ranks(users: List[DBUser], session: Session) -> None:
    for user in users:
        if not user.stats:
            # Create stats if they don't exist
            user.stats = [
                stats.create(user.id, 0, session=session),
                stats.create(user.id, 1, session=session),
                stats.create(user.id, 2, session=session),
                stats.create(user.id, 3, session=session)
            ]

        user.stats.sort(key=lambda s:s.mode)
        utils.sync_ranks(user, session=session)
