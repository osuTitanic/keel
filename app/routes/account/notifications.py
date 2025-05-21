
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import RedirectResponse
from typing import List

from app.common.database import notifications
from app.models import NotificationModel
from app.utils import requires

router = APIRouter()

@router.get("/notifications", response_model=List[NotificationModel])
@requires("authenticated")
def get_notifications(request: Request) -> List[NotificationModel]:
    """Get a list of unread notifications for the authenticated user"""
    return [
        NotificationModel.model_validate(notification, from_attributes=True)
        for notification in notifications.fetch_all(request.user.id, False, session=request.state.db)
    ]

@router.delete("/notifications", response_model=List[NotificationModel])
@requires("users.notifications.delete")
def confirm_all_notifications(request: Request) -> List[NotificationModel]:
    """Confirm all unread notifications for the authenticated user"""
    notifications.update_by_user_id(request.user.id, {'read': True}, request.state.db)
    return RedirectResponse("/account/notifications", status_code=303)

@router.delete("/notifications/{id}", response_model=List[NotificationModel])
@requires("users.notifications.delete")
def confirm_notification(request: Request, id: int) -> List[NotificationModel]:
    """Confirm a specific notification for the authenticated user"""
    if not (notification := notifications.fetch_one(id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested notification could not be found"
        )
    
    if notification.user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    notifications.update(id, {'read': True}, request.state.db)
    return RedirectResponse("/account/notifications", status_code=303)
