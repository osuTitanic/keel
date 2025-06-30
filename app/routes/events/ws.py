
from fastapi.websockets import WebSocketDisconnect
from fastapi import APIRouter, WebSocket
from redis.asyncio.client import PubSub

import asyncio
import app

router = APIRouter()

@router.websocket("/")
async def event_websocket(websocket: WebSocket):
    await websocket.accept()

    pubsub = app.session.redis_async.pubsub()
    await pubsub.subscribe("bancho:events")

    try:
        await event_listener(websocket, pubsub)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("bancho:events")
        await pubsub.close()
        await websocket.close()

async def event_listener(websocket: WebSocket, pubsub: PubSub) -> None:
    while True:
        response = await pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=0
        )

        if response is None:
            continue

        event_name, args, kwargs = eval(response["data"])

        if event_name != "bancho_event":
            continue

        await handle_response(websocket, *args, **kwargs)

async def handle_response(
    websocket: WebSocket,
    user_id: int,
    mode: int | None,
    type: int,
    data: dict,
    is_announcement: bool = False
) -> None:
    await websocket.send_json({
        "user_id": user_id,
        "mode": mode,
        "type": type,
        "data": data
    })
