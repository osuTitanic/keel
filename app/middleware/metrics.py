
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.requests import Request
from typing import Callable

import time
import app

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        start_time = time.perf_counter_ns()
        response = await call_next(request)
        end_time = time.perf_counter_ns()

        time_elapsed = end_time - start_time
        response.headers["process-time"] = str(round(time_elapsed) / 1e6)
        return response

app.api.add_middleware(MetricsMiddleware)
