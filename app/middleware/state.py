
from __future__ import annotations
from fastapi import Request
from typing import Callable
import app

@app.api.middleware("http")
async def state_middleware(request: Request, call_next: Callable):
    with app.session.database.managed_session() as session:
        request.state.db = session
        request.state.redis = app.session.redis
        request.state.logger = app.session.logger
        request.state.events = app.session.events
        request.state.storage = app.session.storage
        request.state.requests = app.session.requests
        return await call_next(request)
