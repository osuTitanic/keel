
from fastapi import HTTPException, APIRouter, Request
from app.models import SubscriptionModel
from app.security import require_login
from app.common.database import users
from app.utils import requires

router = APIRouter(dependencies=[require_login])

@router.get("/subscriptions")
@requires("authenticated")
def get_subscriptions(request: Request):
    subscriptions = users.fetch_subscriptions(
        request.user.id,
        request.state.db
    )

    subscriptions = [
        subscription
        for subscription in subscriptions
        if not subscription.topic.hidden
    ]

    return [
        SubscriptionModel.model_validate(subscription, from_attributes=True)
        for subscription in subscriptions
    ]
