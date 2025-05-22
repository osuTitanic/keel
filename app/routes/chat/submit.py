

from fastapi import HTTPException, APIRouter, Request, Body
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import MessagePostRequest, PrivateMessageModel, MessageModel, ErrorResponse
from app.common.database import channels, groups, messages, users
from app.common.constants.strings import BAD_WORDS
from app.common.database.objects import DBUser
from app.security import require_login
from app.utils import requires

router = APIRouter(
    dependencies=[require_login],
    responses={
        404: {"model": ErrorResponse, "description": "Channel not found"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        400: {"model": ErrorResponse, "description": "Invalid request data"}
    }
)

@router.post("/channels/{target}/messages", response_model=MessageModel)
@requires(["chat.messages.create"])
def post_message(
    target: str,
    request: Request,
    data: MessagePostRequest = Body(...)
) -> MessageModel:
    if not (channel := channels.fetch_one(target, request.state.db)):
        raise HTTPException(404, 'The requested channel could not be found')

    user_permissions = groups.get_player_permissions(
        request.user.id,
        request.state.db
    )

    if user_permissions < channel.read_permissions:
        raise HTTPException(403, 'Insufficient permissions')

    if user_permissions < channel.write_permissions:
        raise HTTPException(403, 'Insufficient permissions')

    has_bad_words = any([
        word in data.message.lower()
        for word in BAD_WORDS
    ])

    if has_bad_words and not request.user.is_bot:
        silence_user(request.user.id, 60*10, request.state.db)
        raise HTTPException(400, 'Message contains offensive language')

    # TODO: Check if channel is moderated
    # TODO: Check for message spamming

    message = messages.create(
        request.user.name,
        channel.name,
        data.message,
        request.state.db
    )
    message.sender = request.user

    request.state.events.submit(
        'external_message',
        sender_id=request.user.id,
        sender=request.user.name,
        target=channel.name,
        message=data.message
    )

    return MessageModel.model_validate(
        message,
        from_attributes=True
    )

@router.post("/dms/{target_id}/messages", response_model=PrivateMessageModel)
@requires(["chat.messages.private.create"])
def post_private_message(
    target_id: int,
    request: Request,
    data: MessagePostRequest = Body(...)
) -> PrivateMessageModel:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(404, 'Target user could not be found')

    if is_user_silenced(target):
        raise HTTPException(400, 'Target is silenced')

    if target.id == request.user.id:
        raise HTTPException(400, 'Cannot send messages to yourself')

    # TODO: Check for message spamming
    # TODO: Check if target blocked user / has friend-only dms

    message = messages.create_private(
        request.user.id,
        target.id,
        data.message,
        request.state.db
    )

    request.state.events.submit(
        'external_dm',
        sender_id=request.user.id,
        target_id=target.id,
        message=data.message
    )

    return PrivateMessageModel.model_validate(
        message,
        from_attributes=True
    )

def silence_user(user: DBUser, duration: int, request: Request):
    silence_offset = (
        user.silence_end or datetime.now()
    )

    users.update(
        user.id,
        {"silence_end": silence_offset + timedelta(seconds=duration)},
        session=request.state.db
    )

    # Send 'silence' event to bancho
    request.state.events.submit(
        'silence',
        user_id=user.id,
        duration=duration,
        reason='Auto-silenced for using offensive language in chat.'
    )

def is_user_silenced(user: DBUser) -> bool:
    return user.silence_end and user.silence_end > datetime.now()
