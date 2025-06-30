
from fastapi import HTTPException, APIRouter, Request, Body
from typing import List

from app.models import SubscriptionModel, SubscriptionRequest, ErrorResponse
from app.common.constants import UserActivity
from app.common.database import users, topics
from app.common.helpers import activity
from app.security import require_login
from app.utils import requires

router = APIRouter(
    dependencies=[require_login],
    responses={
        404: {"description": "Subscription/Topic not found", "model": ErrorResponse}
    }
)

@router.get("/subscriptions", response_model=List[SubscriptionModel])
@requires("users.authenticated")
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

@router.get("/subscriptions/{topic_id}", response_model=SubscriptionModel)
@requires("users.authenticated")
def get_subscription(request: Request, topic_id: int):
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    subscription = topics.fetch_subscriber(
        topic_id,
        request.user.id,
        request.state.db
    )

    if not subscription:
        raise HTTPException(404, "The requested subscription could not be found")

    return SubscriptionModel.model_validate(subscription, from_attributes=True)

@router.post("/subscriptions", response_model=SubscriptionModel)
@requires("forum.subscriptions.create")
def create_subscription(request: Request, data: SubscriptionRequest = Body(...)):
    if not (topic := topics.fetch_one(data.topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    subscription = topics.add_subscriber(
        topic.id,
        request.user.id,
        request.state.db
    )

    activity.submit(
        request.user.id, None,
        UserActivity.ForumSubscribed,
        {
            'username': request.user.name,
            'topic_name': topic.title,
            'topic_id': topic.id
        },
        is_hidden=True,
        session=request.state.db
    )

    return SubscriptionModel.model_validate(subscription, from_attributes=True)

@router.delete("/subscriptions/{topic_id}")
@requires("forum.subscriptions.delete")
def delete_subscription(request: Request, topic_id: int) -> dict:
    if not (topic := topics.fetch_one(topic_id, request.state.db)):
        raise HTTPException(404, "The requested topic could not be found")

    if topic.hidden:
        raise HTTPException(404, "The requested topic could not be found")

    rows = topics.delete_subscriber(
        topic.id,
        request.user.id,
        request.state.db
    )

    if not rows:
        raise HTTPException(404, "The requested subscription could not be found")

    activity.submit(
        request.user.id, None,
        UserActivity.ForumUnsubscribed,
        {
            'username': request.user.name,
            'topic_name': topic.title,
            'topic_id': topic.id
        },
        is_hidden=True,
        session=request.state.db
    )

    return {}
