
from fastapi import HTTPException, APIRouter, Request, Body
from app.models import PlaystyleRequestModel, PlaystyleResponseModel
from app.common.database.repositories import users
from app.common.constants import Playstyle

router = APIRouter()

@router.get("/{user_id}/playstyle")
def get_user_playstyle(request: Request, user_id: int) -> PlaystyleResponseModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    if not user.activated:
        raise HTTPException(
            status_code=404,
            detail='The requested user could not be found'
        )

    return PlaystyleResponseModel(playstyle=user.playstyle)

@router.post("/{user_id}/playstyle")
def add_playstyle(
    request: Request,
    user_id: int,
    data: PlaystyleRequestModel = Body(...)
) -> PlaystyleResponseModel:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    new_playstyle = (
        Playstyle(request.user.playstyle) | Playstyle[data.playstyle]
    )

    users.update(
        user.id,
        {'playstyle': new_playstyle.value},
        request.state.db
    )

    return PlaystyleResponseModel(playstyle=new_playstyle.value)

@router.delete("/{user_id}/playstyle")
def remove_playstyle(
    request: Request,
    user_id: int,
    data: PlaystyleRequestModel = Body(...)
) -> PlaystyleResponseModel:
    if user_id != request.user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action"
        )

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(
            status_code=404,
            detail="The requested user could not be found"
        )

    new_playstyle = (
        Playstyle(user.playstyle) & ~Playstyle[data.playstyle]
    )

    users.update(
        user.id,
        {'playstyle': new_playstyle.value},
        request.state.db
    )

    return PlaystyleResponseModel(playstyle=new_playstyle.value)
