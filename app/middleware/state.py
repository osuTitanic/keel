
from starlette.types import ASGIApp, Receive, Scope, Send
from app import api, session

class StateMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        with session.database.managed_session() as database_session:
            state = scope.setdefault("state", {})
            state["db"] = database_session
            state["redis"] = session.redis
            state["logger"] = session.logger
            state["events"] = session.events
            state["storage"] = session.storage
            state["requests"] = session.requests
            state["redis_async"] = session.redis_async
            await self.app(scope, receive, send)

api.add_middleware(StateMiddleware)
