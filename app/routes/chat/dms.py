
from fastapi import HTTPException, APIRouter, Request, Query
from typing import List

from app.models import PrivateMessageSelectionEntry, PrivateMessageModel, UserModelCompact
from app.common.database import messages, users
from app.security import require_login
from app.utils import requires

router = APIRouter(dependencies=[require_login])

@router.get('/dms', response_model=List[PrivateMessageSelectionEntry])
@requires('authenticated')
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

@router.get('/dms/{target_id}/messages', response_model=List[PrivateMessageModel])
@requires('authenticated')
def direct_message_history(
    request: Request,
    target_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50)
) -> List[PrivateMessageModel]:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(404, 'User not found')

    user_messages = messages.fetch_dms(
        request.user.id, target.id,
        limit, offset,
        request.state.db
    )

    return [
        PrivateMessageModel.model_validate(message, from_attributes=True)
        for message in user_messages
    ]
