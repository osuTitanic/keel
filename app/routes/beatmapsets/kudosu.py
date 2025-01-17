
from app.models import KudosuWithoutSetModel, ErrorResponse
from app.common.database import beatmapsets, modding, posts
from fastapi import APIRouter, HTTPException, Request
from typing import List

router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "The requested beatmap could not be found"},
        404: {"model": ErrorResponse, "description": "The requested post could not be found"}
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
