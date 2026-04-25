
from fastapi.websockets import WebSocketDisconnect, WebSocketState
from fastapi import APIRouter, WebSocket
from redis.asyncio.client import PubSub
from app.security import require_login
from typing import Any, Tuple, Dict
from app.utils import requires

import logging
import json
import app

router = APIRouter()
logger = logging.getLogger("ws")

@router.websocket("/ws", dependencies=[require_login])
@requires("bancho.events.view")
async def event_websocket(websocket: WebSocket):
    await websocket.accept()

    # Close existing unused database session
    websocket.state.db.close()

    try:
        pubsub = app.session.redis_async.pubsub()
        await pubsub.subscribe("bancho:events")
        await event_listener(websocket, pubsub)
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        # ASGI flow error: Transport not initialized or closed
        pass
    except Exception as e:
        logger.error(f"Error in event connection: {e}", exc_info=True)
    finally:
        await pubsub.unsubscribe("bancho:events")
        await pubsub.close()

        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close()

async def event_listener(websocket: WebSocket, pubsub: PubSub) -> None:
    while True:
        response = await pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=None
        )

        if response is None:
            continue

        decoded = decode_event(response["data"])

        if decoded is None:
            continue

        event_name, args, kwargs = decoded

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

def decode_event(data: Any) -> Tuple[str, Tuple, Dict] | None:
    """Decode an event payload from pubsub safely."""
    try:
        payload = json.loads(data)
    except (TypeError, json.JSONDecodeError) as e:
        return None

    if not isinstance(payload, dict):
        return None

    name = payload.get('event')
    args = payload.get('args', [])
    kwargs = payload.get('kwargs', {})

    if not isinstance(name, str):
        return None

    if not isinstance(args, (list, tuple)):
        return None

    if not isinstance(kwargs, dict):
        return None

    return name, tuple(args), kwargs
