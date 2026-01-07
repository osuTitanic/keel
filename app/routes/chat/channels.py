
from fastapi import HTTPException, APIRouter, Request, Query
from collections import defaultdict
from sqlalchemy.orm import Session
from typing import Iterable, List

from app.common.database import messages, channels, names, groups, users
from app.models import MessageModel, ChannelModel, ErrorResponse
from app.common.database.objects import DBUser, DBMessage
from app.security import require_login
from app.utils import requires

router = APIRouter(dependencies=[require_login])
responses = {
    404: {"model": ErrorResponse, "description": "Channel not found"},
    403: {"model": ErrorResponse, "description": "Insufficient permissions"}
}

@router.get("/channels", response_model=List[ChannelModel])
@requires("chat.messages.view")
def channel_selection(
    request: Request,
    has_participated: bool = Query(False)
) -> List[ChannelModel]:
    if has_participated:
        return [
            ChannelModel.model_validate(channel, from_attributes=True)
            for channel in channels.fetch_channel_entries(request.user.name, request.state.db)
        ]

    permissions = groups.fetch_bancho_permissions(
        request.user.id,
        request.state.db
    )

    return [
        ChannelModel.model_validate(channel, from_attributes=True)
        for channel in channels.fetch_by_permissions(permissions, request.state.db)
    ]

@router.get("/channels/{target}", response_model=ChannelModel, responses=responses)
@requires("chat.messages.view")
def get_channel(
    request: Request,
    target: str
) -> ChannelModel:
    if not (channel := channels.fetch_one(target, request.state.db)):
        raise HTTPException(404, 'The requested channel could not be found')

    user_permissions = groups.fetch_bancho_permissions(
        request.user.id,
        request.state.db
    )

    if user_permissions < channel.read_permissions:
        raise HTTPException(403, 'Insufficient permissions')

    return ChannelModel.model_validate(
        channel,
        from_attributes=True
    )

@router.get("/channels/{target}/messages", response_model=List[MessageModel], responses=responses)
@requires("chat.messages.view")
def channel_message_history(
    request: Request,
    target: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> List[MessageModel]:
    if not (channel := channels.fetch_one(target, request.state.db)):
        raise HTTPException(404, 'The requested channel could not be found')

    user_permissions = groups.fetch_bancho_permissions(
        request.user.id,
        request.state.db
    )

    if user_permissions < channel.read_permissions:
        raise HTTPException(403, 'Insufficient permissions')

    channel_messages = messages.fetch_recent(
        target, limit, offset,
        request.state.db
    )

    return resolve_message_users(
        channel_messages,
        request
    )

def resolve_message_users(messages: List[DBMessage], request: Request) -> Iterable[MessageModel]:
    sender_cache = defaultdict(lambda: None)

    for message in messages:
        response = MessageModel(
            id=message.id,
            sender=None,
            sender_name=message.sender,
            message=message.message,
            time=message.time,
        )

        if message.sender in sender_cache:
            response.sender = sender_cache[message.sender]
            yield response
            continue

        sender = resolve_user(
            message.sender,
            request.state.db
        )

        if not sender:
            sender_cache[message.sender] = None
            response.sender = None
            yield response
            continue

        sender_cache[message.sender] = sender
        response.sender = sender
        yield response

def resolve_user(username: str, session: Session) -> DBUser | None:
    safe_name = username.lower().replace(' ', '_')

    if user := users.fetch_by_safe_name(safe_name, session):
        return user

    if name_change := names.fetch_by_name_extended(username, session):
        return name_change.user
