
from fastapi import HTTPException, APIRouter, Request
from app.models import NameHistoryModel, NameHistoryUpdateRequest, NameChangeRequest
from app.common.database import names, users
from app.utils import requires
from typing import List

router = APIRouter()

@router.get("/names", response_model=List[NameHistoryModel])
@requires("users.moderation.names")
def get_user_name_history(request: Request, user_id: int) -> List[NameHistoryModel]:
    return [
        NameHistoryModel.model_validate(name, from_attributes=True)
        for name in names.fetch_all(user_id, request.state.db)
    ]

@router.post("/names", response_model=NameHistoryModel)
@requires("users.moderation.names.create")
def change_user_name(
    request: Request,
    user_id: int,
    data: NameChangeRequest
) -> NameHistoryModel:
    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    safe_name = data.name.lower().replace(" ", "_")

    if users.fetch_by_safe_name(safe_name, session=request.state.db):
        raise HTTPException(400, "This name is already in use")

    entry = names.create(user.id, user.name)
    success = users.update(user.id, {'name': data.name, 'safe_name': safe_name})

    if not success:
        raise HTTPException(500, "Failed to update user name")

    return NameHistoryModel.model_validate(
        entry,
        from_attributes=True
    )

@router.patch("/names/{id}", response_model=NameHistoryModel)
@requires("users.moderation.names.update")
def update_name_history(
    request: Request,
    user_id: int,
    id: int,
    update: NameHistoryUpdateRequest
) -> NameHistoryModel:
    if not (entry := names.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Name history entry not found")

    if entry.user_id != user_id:
        raise HTTPException(400, "Name history entry does not belong to the specified user")

    success = names.update(
        entry.id,
        {
            "name": update.name,
            "reserved": update.reserved
        },
        request.state.db
    )

    if not success:
        raise HTTPException(500, "Failed to update name history entry")

    # Refresh name entry
    request.state.db.refresh(entry)    

    return NameHistoryModel.model_validate(
        entry,
        from_attributes=True
    )

@router.delete("/names/{id}", response_model=NameHistoryModel)
@requires("users.moderation.names.delete")
def delete_name_history_entry(
    request: Request,
    user_id: int,
    id: int
) -> NameHistoryModel:
    if not (entry := names.fetch_one(id, request.state.db)):
        raise HTTPException(404, "Name history entry not found")

    if entry.user_id != user_id:
        raise HTTPException(400, "Name history entry does not belong to the specified user")

    success = names.delete(id, request.state.db)

    if not success:
        raise HTTPException(500, "Failed to delete name history entry")

    return NameHistoryModel.model_validate(
        entry,
        from_attributes=True
    )
