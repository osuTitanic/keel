
from fastapi import HTTPException, APIRouter, Request, Query
from typing import List

from app.models import PrivateMessageSelectionEntry, PrivateMessageModel, UserModelCompact, ErrorResponse
from app.common.database import messages, users
from app.security import require_login
from app.utils import requires

router = APIRouter(dependencies=[require_login])
responses = {404: {'model': ErrorResponse, 'description': "User not found"}}

@router.get("/dms", response_model=List[PrivateMessageSelectionEntry])
@requires("chat.messages.private.view")
def direct_message_selection(request: Request) -> List[PrivateMessageSelectionEntry]:
    user_list = messages.fetch_dm_entries(
        request.user.id,
        request.state.db
    )

    entries = [
        PrivateMessageSelectionEntry(
            user=UserModelCompact.model_validate(
                user,
                from_attributes=True
            ),
            last_message=PrivateMessageModel.model_validate(
                messages.fetch_last_dm(user.id, request.user.id, request.state.db),
                from_attributes=True
            )
        )
        for user in user_list
    ]

    return sorted(entries, key=lambda x: x.last_message.id, reverse=True)

@router.get("/dms/{target_id}/messages", response_model=List[PrivateMessageModel], responses=responses)
@requires("chat.messages.private.view")
def direct_message_history(
    request: Request,
    target_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> List[PrivateMessageModel]:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(404, 'The requested user could not be found')

    user_messages = messages.fetch_dms(
        request.user.id, target.id,
        limit, offset,
        request.state.db
    )

    return [
        PrivateMessageModel.model_validate(message, from_attributes=True)
        for message in user_messages
    ]

@router.post("/dms/{target_id}/messages/{message_id}/read", response_model=PrivateMessageModel, responses=responses)
@requires("chat.messages.private.view")
def mark_dm_as_read(
    request: Request,
    target_id: int,
    message_id: int
) -> PrivateMessageModel:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(404, 'The requested user could not be found')

    if not (message := messages.fetch_dm(message_id, session=request.state.db)):
        raise HTTPException(404, 'The requested message could not be found')

    if request.user.id != message.target_id:
        raise HTTPException(404, 'You cannot mark messages to this user as read')

    if target.id != message.sender_id:
        raise HTTPException(404, 'You cannot mark messages from this user as read')

    messages.update_private(
        message.id,
        {'read': True},
        request.state.db
    )
    request.state.db.refresh(message)

    return PrivateMessageModel.model_validate(message, from_attributes=True)

@router.post("/dms/{target_id}/messages/read", response_model=List[PrivateMessageModel], responses=responses)
@requires("chat.messages.private.view")
def mark_all_dms_as_read(
    request: Request,
    target_id: int
) -> List[PrivateMessageModel]:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(404, 'The requested user could not be found')

    messages.update_private_all(
        target.id,
        request.user.id,
        {'read': True},
        request.state.db
    )

    user_messages = messages.fetch_dms(
        request.user.id, target.id,
        limit=15, offset=0,
        session=request.state.db
    )

    return [
        PrivateMessageModel.model_validate(message, from_attributes=True)
        for message in user_messages
    ]
