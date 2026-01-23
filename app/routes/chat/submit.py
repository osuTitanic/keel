

from fastapi import HTTPException, APIRouter, Request, Body
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import MessagePostRequest, PrivateMessageModel, MessageModel, ErrorResponse
from app.common.database import channels, groups, messages, users, relationships
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
@requires("chat.messages.create")
def post_message(
    target: str,
    request: Request,
    data: MessagePostRequest = Body(...)
) -> MessageModel:
    if not (channel := channels.fetch_one(target, request.state.db)):
        request.state.logger.warning(
            f"'{request.user.name}' attempted to post message to nonexistent channel '{target}'"
        )
        raise HTTPException(404, 'The requested channel could not be found')

    user_permissions = groups.fetch_bancho_permissions(
        request.user.id,
        request.state.db
    )

    if user_permissions < channel.read_permissions:
        request.state.logger.warning(
            f"'{request.user.name}' attempted to post message to {channel.name} without read permissions"
        )
        raise HTTPException(403, 'Insufficient permissions')

    if user_permissions < channel.write_permissions:
        request.state.logger.warning(
            f"'{request.user.name}' attempted to post message to {channel.name} without write permissions"
        )
        raise HTTPException(403, 'Insufficient permissions')

    data.message, timeout = request.state.filters.apply(data.message)

    if timeout is not None:
        silence_user(request.user, timeout, request.state, channel.name)
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
    request.state.logger.info(
        f"'{request.user.name}' posted message to channel '{channel.name}'"
    )

    return MessageModel(
        id=message.id,
        sender=request.user,
        sender_name=request.user.name,
        message=message.message,
        time=message.time
    )

@router.post("/dms/{target_id}/messages", response_model=PrivateMessageModel)
@requires("chat.messages.private.create")
def post_private_message(
    target_id: int,
    request: Request,
    data: MessagePostRequest = Body(...)
) -> PrivateMessageModel:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        request.state.logger.warning(
            f"'{request.user.name}' attempted to send a DM to nonexistent user '{target_id}'"
        )
        raise HTTPException(404, 'Target user could not be found')

    if target.id == request.user.id:
        request.state.logger.warning(
            f"'{request.user.name}' attempted to send a DM to themselves"
        )
        raise HTTPException(400, 'Cannot send messages to yourself')

    if is_user_silenced(target):
        request.state.logger.warning(
            f"'{request.user.name}' attempted to send a DM to silenced user '{target.name}'"
        )
        raise HTTPException(400, 'Target user is silenced')

    target_blocked_sender = relationships.is_blocked(
        target.id,
        request.user.id,
        session=request.state.db
    )

    if target_blocked_sender:
        request.state.logger.warning(
            f"'{request.user.name}' attempted to send a DM to blocked user '{target.name}'"
        )
        raise HTTPException(400, 'The target user is not accepting messages from you')

    sender_bocked_target = relationships.is_blocked(
        request.user.id,
        target.id,
        session=request.state.db
    )

    if sender_bocked_target:
        request.state.logger.warning(
            f"'{request.user.name}' attempted to send a DM to user '{target.name}' who they have blocked"
        )
        raise HTTPException(400, 'You are not accepting messages from the target user')

    data.message, timeout = request.state.filters.apply(data.message)

    if timeout is not None:
        silence_user(request.user, timeout, request.state, "pms")
        raise HTTPException(400, 'Message contains offensive language')

    # TODO: Check for message spamming
    # TODO: Check if target has friend-only dms

    message = messages.create_private(
        request.user.id,
        target.id,
        data.message,
        read=False,
        session=request.state.db
    )

    request.state.events.submit(
        'external_dm',
        sender_id=request.user.id,
        target_id=target.id,
        message=data.message,
        message_id=message.id
    )
    request.state.logger.info(
        f"'{request.user.name}' sent a DM to user '{target.name}'"
    )

    return PrivateMessageModel.model_validate(
        message,
        from_attributes=True
    )

def silence_user(user: DBUser, duration: int, request: Request, target: str):
    request.state.logger.warning(
        f"Silencing user '{user.name}' for {duration} seconds "
        f"due to inappropriate discussion in {target}"
    )
    request.state.events.submit(
        'silence',
        user_id=user.id,
        duration=duration,
        reason=f'Inappropriate discussion in {target}'
    )

def is_user_silenced(user: DBUser) -> bool:
    return user.silence_end and user.silence_end > datetime.now()
