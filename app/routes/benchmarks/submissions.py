from fastapi import APIRouter, Request, Query
from app.common.database import benchmarks
from app.models import BenchmarkModel
from typing import List

router = APIRouter()

@router.get("/submissions", response_model=List[BenchmarkModel])
def get_benchmark_submissions(
    request: Request,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[BenchmarkModel]:
    return [
        BenchmarkModel.model_validate(
            benchmark,
            from_attributes=True
        )
        for benchmark in benchmarks.fetch_range(
            offset,
            limit,
            request.state.db
        )
    ]
