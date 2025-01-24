
from fastapi import HTTPException, APIRouter, Request, Query
from typing import List

from app.common.database import messages, users
from app.models import PrivateMessageModel
from app.utils import requires

router = APIRouter()

@router.get('/dms/{target_id}/messages', response_model=List[PrivateMessageModel])
@requires('authenticated')
def direct_message_history(
    request: Request,
    target_id: int,
    offset: int = Query(0, ge=0),
) -> List[PrivateMessageModel]:
    if not (target := users.fetch_by_id(target_id, session=request.state.db)):
        raise HTTPException(404, 'User not found')

    user_messages = messages.fetch_dms(
        request.user.id, target.id,
        50, offset,
        request.state.db
    )

    return [
        PrivateMessageModel.model_validate(message, from_attributes=True)
        for message in user_messages
    ]
