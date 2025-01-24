
from fastapi import HTTPException, APIRouter, Request, Query
from collections import defaultdict
from sqlalchemy.orm import Session
from typing import List

from app.common.database import messages, channels, names, groups, users
from app.common.database.objects import DBUser
from app.security import require_login
from app.models import MessageModel
from app.utils import requires

router = APIRouter(dependencies=[require_login])

@router.get('/channels/{target}/messages', response_model=List[MessageModel])
@requires('authenticated')
def channel_message_history(
    request: Request,
    target: str,
    offset: int = Query(0, ge=0),
) -> List[MessageModel]:
    if not (channel := channels.fetch_one(target, request.state.db)):
        raise HTTPException(404, 'Channel not found')

    user_permissions = groups.get_player_permissions(
        request.user.id,
        request.state.db
    )

    if user_permissions < channel.read_permissions:
        raise HTTPException(403, 'Insufficient permissions')

    channel_messages = messages.fetch_recent(
        target, 50, offset,
        request.state.db
    )

    channel_messages = resolve_message_users(
        channel_messages, request
    )

    return [
        MessageModel.model_validate(message, from_attributes=True)
        for message in channel_messages
    ]

def resolve_message_users(messages: List[MessageModel], request: Request) -> List[MessageModel]:
    sender_cache = defaultdict(lambda: None)

    for message in messages:
        if message.sender in sender_cache:
            message.sender = sender_cache[message.sender]
            continue

        sender = resolve_user(
            message.sender,
            request.state.db
        )

        if not sender:
            sender_cache[message.sender] = None
            continue

        # Preload relationships for user model
        load_relationships(
            'relationships',
            'achievements',
            'groups',
            'badges',
            'names',
            'stats',
            model=sender
        )

        sender_cache[message.sender] = sender
        message.sender = sender

    del sender_cache
    return messages

def resolve_user(username: str, session: Session) -> DBUser | None:
    if user := users.fetch_by_name_extended(username, session):
        return user

    if name_change := names.fetch_by_name_extended(username, session):
        return name_change.user

def load_relationships(*relationships, model):
    for relationship in relationships:
        getattr(model, relationship)
