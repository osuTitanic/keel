from fastapi import APIRouter, Request, Query
from app.common.database.objects import DBBenchmark
from app.models import BenchmarkModel
from typing import List

router = APIRouter()

@router.get("/submissions", response_model=List[BenchmarkModel])
def get_benchmark_submissions(
    request: Request,
    limit: int = Query(100, ge=1, le=100),
    before_id: int | None = Query(None, ge=1)
) -> List[BenchmarkModel]:
    query = request.state.db.query(DBBenchmark)
    if before_id is not None:
        query = query.filter(DBBenchmark.id < before_id)

    benchmarks = query.order_by(DBBenchmark.id.desc()).limit(limit).all()
    return [BenchmarkModel.model_validate(benchmark, from_attributes=True) for benchmark in benchmarks]
