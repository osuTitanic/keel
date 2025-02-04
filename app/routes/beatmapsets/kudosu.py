
from fastapi import APIRouter, HTTPException, Request
from datetime import timedelta
from typing import List

from app.models import KudosuModel, KudosuWithoutSetModel, ErrorResponse
from app.common.database import beatmapsets, modding, posts
from app.common.constants import DatabaseStatus
from app.security import require_login
from app.utils import requires

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "The requested beatmap could not be found"},
        404: {"model": ErrorResponse, "description": "The requested post could not be found"},
    }
)

@router.get("/{set_id}/kudosu", response_model=List[KudosuWithoutSetModel])
def get_kudosu_by_set(request: Request, set_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    kudosu = modding.fetch_all_by_set(
        set_id=beatmapset.id,
        session=request.state.db
    )

    return [
        KudosuWithoutSetModel.model_validate(k, from_attributes=True)
        for k in kudosu
    ]

@router.get("/{set_id}/kudosu/{post_id}", response_model=List[KudosuWithoutSetModel])
def get_kudosu_by_post(request: Request, set_id: int, post_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested post could not be found"
        )

    if post.topic_id != beatmapset.topic_id:
        raise HTTPException(
            status_code=404,
            detail="The requested post could not be found"
        )

    kudosu = modding.fetch_all_by_post(
        post_id=post.id,
        session=request.state.db
    )

    return [
        KudosuWithoutSetModel.model_validate(k, from_attributes=True)
        for k in kudosu
    ]

@router.post("/{set_id}/kudosu/{post_id}/reward", response_model=KudosuModel, dependencies=[require_login])
@requires("authenticated")
def reward_kudosu(request: Request, set_id: int, post_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if not beatmapset.topic_id:
        raise HTTPException(
            status_code=400,
            detail="This beatmapset is not linked to a forum topic"
        )

    is_authorized = (
        request.user.id != beatmapset.creator_id or
        request.user.is_bat
    )

    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if beatmapset.status >= DatabaseStatus.Ranked:
        raise HTTPException(
            status_code=400,
            detail="This beatmapset is already ranked"
        )

    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested post could not be found"
        )

    if post.user_id == request.user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot reward kudosu on your own post"
        )

    if post.user_id == beatmapset.creator_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot reward kudosu to the beatmapset creator"
        )

    existing_mod = modding.fetch_by_post_and_sender(
        post_id,
        request.user.id,
        request.state.db
    )

    if existing_mod:
        raise HTTPException(
            status_code=400,
            detail="Kudosu was already rewarded to this post"
        )

    previous_post = posts.fetch_previous(
        post_id,
        beatmapset.topic_id,
        request.state.db
    )

    if not previous_post:
        raise HTTPException(
            status_code=400,
            detail="This post is the first post in the topic"
        )

    delta = (
        post.created_at - previous_post.created_at
    )

    kudosu_amount = (
        1 if delta < timedelta(days=7)
        else 2
    )

    kudosu = modding.create(
        target_id=post.user_id,
        sender_id=request.user.id,
        set_id=set_id,
        post_id=post_id,
        amount=kudosu_amount,
        session=request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {'star_priority': max(beatmapset.star_priority + kudosu_amount, 0)},
        request.state.db
    )

    return KudosuModel.model_validate(kudosu, from_attributes=True)

@router.post("/{set_id}/kudosu/{post_id}/revoke", response_model=KudosuModel, dependencies=[require_login])
@requires("bat")
def revoke_kudosu(request: Request, set_id: int, post_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if not beatmapset.topic_id:
        raise HTTPException(
            status_code=400,
            detail="This beatmapset is not linked to a forum topic"
        )

    if beatmapset.status >= DatabaseStatus.Ranked:
        raise HTTPException(
            status_code=400,
            detail="This beatmapset is already ranked"
        )

    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested post could not be found"
        )

    if post.user_id == request.user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot revoke kudosu on your own post"
        )

    if post.user_id == beatmapset.creator_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot revoke kudosu from the beatmapset creator"
        )

    total_kudosu = modding.total_amount(
        post_id=post.id,
        session=request.state.db
    )

    if total_kudosu < 0:
        raise HTTPException(
            status_code=400,
            detail="This post has already been revoked"
        )

    existing_mod = modding.fetch_by_post_and_sender(
        post_id,
        beatmapset.creator_id,
        request.state.db
    )

    if existing_mod:
        modding.delete(
            existing_mod.id,
            request.state.db
        )

    kudosu = modding.create(
        target_id=post.user_id,
        sender_id=request.user.id,
        set_id=set_id,
        post_id=post_id,
        amount=min(-1, -total_kudosu),
        session=request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {'star_priority': max(beatmapset.star_priority + kudosu.amount, 0)},
        session=request.state.db
    )

    return KudosuModel.model_validate(kudosu, from_attributes=True)

@router.post("/{set_id}/kudosu/{post_id}/reset", dependencies=[require_login])
@requires("bat")
def reset_kudosu(request: Request, set_id: int, post_id: int):
    if not (beatmapset := beatmapsets.fetch_one(set_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested beatmapset could not be found"
        )

    if not beatmapset.topic_id:
        raise HTTPException(
            status_code=400,
            detail="This beatmapset is not linked to a forum topic"
        )

    if not (post := posts.fetch_one(post_id, request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested post could not be found"
        )

    if post.user_id == request.user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot reset kudosu on your own post"
        )
    
    if post.user_id == beatmapset.creator_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot reset kudosu from the beatmapset creator"
        )

    total_entries = modding.total_entries(
        post_id,
        request.state.db
    )

    if total_entries == 0:
        raise HTTPException(
            status_code=404,
            detail="This post has no kudosu exchanges"
        )
    
    total_kudosu = modding.total_amount(
        post_id,
        request.state.db
    )

    modding.delete_by_post(
        post_id,
        request.state.db
    )

    beatmapsets.update(
        beatmapset.id,
        {'star_priority': max(beatmapset.star_priority - total_kudosu, 0)},
        request.state.db
    )

    return {}
