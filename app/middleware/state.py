
from __future__ import annotations
from fastapi import Request
from typing import Callable
import app

@app.api.middleware("http")
async def state_middleware(request: Request, call_next: Callable):
    with app.session.database.managed_session() as session:
        request.state.db = session
        request.state.redis = app.session.redis
        request.state.storage = app.session.storage
        return await call_next(request)
