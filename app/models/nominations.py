
from app.models.user import UserModel
from pydantic import BaseModel

class NominationModel(BaseModel):
    set_id: int
    user_id: int
    created_at: str
    user: UserModel
