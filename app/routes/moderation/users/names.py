
from fastapi import HTTPException, APIRouter, Request
from app.models import NameHistoryModel, NameHistoryUpdateRequest, NameChangeRequest
from app.common.database import names, users
from app.common.constants import regexes
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
    new_name = data.name.strip()
    safe_name = new_name.lower().replace(" ", "_")

    if len(new_name) < 3:
        raise HTTPException(400, "Usernames must be at least 3 characters long")

    if len(new_name) > 15:
        raise HTTPException(400, "Usernames cannot be longer than 15 characters")

    if new_name.lower().endswith("_old"):
        raise HTTPException(400, "Usernames cannot end with `_old`")

    if new_name.lower().startswith("deleteduser"):
        raise HTTPException(400, "This username is not allowed")

    if not regexes.USERNAME.match(new_name):
        raise HTTPException(400, "This username contains invalid characters")

    if not (user := users.fetch_by_id(user_id, session=request.state.db)):
        raise HTTPException(404, "User not found")

    if users.fetch_by_safe_name(safe_name, session=request.state.db):
        raise HTTPException(400, "This name is already in use")

    if reserved_name := names.fetch_by_name_reserved(new_name, request.state.db):
        if reserved_name.user_id != user.id:
            raise HTTPException(400, "This username is reserved by another user")

    past_names = names.fetch_all(user.id, request.state.db)
    max_name_changes = 4

    if len(past_names) >= max_name_changes:
        # Match the bot's policy: release the oldest history entry.
        oldest_entry = min(past_names, key=lambda name: name.id)
        names.update(oldest_entry.id, {"reserved": False})

    entry = names.create(user.id, user.name)
    success = users.update(user.id, {'name': new_name, 'safe_name': safe_name})

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
