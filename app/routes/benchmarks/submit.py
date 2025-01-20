
from __future__ import annotations
from fastapi import APIRouter, Request, Body
from datetime import datetime

from app.models import BenchmarkSubmissionRequest, BenchmarkModel
from app.common.database import benchmarks, users
from app.utils import requires

router = APIRouter()

@router.post('/', response_model=BenchmarkModel)
@requires(['authenticated', 'unrestricted', 'unsilenced', 'activated'])
def post_benchmark_score(request: Request, body: BenchmarkSubmissionRequest = Body(...)):
    benchmark = benchmarks.create(
        user_id=request.user.id,
        smoothness=body.smoothness,
        framerate=body.framerate,
        score=body.raw_score,
        grade=body.grade,
        client=body.client,
        hardware=body.hardware.model_dump(),
        session=request.state.db
    )

    users.update(
        request.user.id,
        {'latest_activity': datetime.now()},
        request.state.db
    )

    return BenchmarkModel.model_validate(benchmark, from_attributes=True)
