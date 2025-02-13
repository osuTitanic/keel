
from app.common.constants import COUNTRIES
from app.common.cache import leaderboards
from app.models import (
    CountryEntryModel,
    CountryStatsModel,
    ModeAlias
)

from fastapi import Request, APIRouter
from typing import List

router = APIRouter()

@router.get("/country/{mode}", response_model=List[CountryEntryModel])
def get_country_rankings(request: Request, mode: ModeAlias) -> List[CountryEntryModel]:
    return [
        CountryEntryModel(
            index=index + 1,
            country_acronym=country['name'],
            country_name=resolve_country_name(country['name']),
            stats=resolve_country_stats(country)
        )
        for index, country in enumerate(leaderboards.top_countries(mode.integer))
    ]

def resolve_country_stats(country: dict) -> CountryStatsModel:
    return CountryStatsModel(
        average_performance=country['average_pp'],
        total_performance=country['total_performance'],
        total_rscore=country['total_rscore'],
        total_tscore=country['total_tscore'],
        total_users=country['total_users']
    )

def resolve_country_name(acronym: str) -> str:
    return COUNTRIES.get(acronym.upper(), 'Unknown')
