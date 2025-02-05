
from fastapi import APIRouter, Request, Query
from app.common.database import benchmarks
from app.models import BenchmarkModel
from typing import List

router = APIRouter()

@router.get("/", response_model=List[BenchmarkModel])
def get_benchmark_leaderboard(
    request: Request,
    page: int = Query(1, ge=0),
    limit: int = Query(50, ge=0, le=50)
) -> List[BenchmarkModel]:
    return [
        BenchmarkModel.model_validate(benchmark, from_attributes=True).model_dump()
        for benchmark in benchmarks.fetch_leaderboard(
            limit=limit,
            offset=(page - 1) * limit,
            session=request.state.db
        )
    ]
