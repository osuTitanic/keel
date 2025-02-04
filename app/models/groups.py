
from pydantic import BaseModel

class GroupModel(BaseModel):
    id: int
    name: str
    short_name: str
    description: str | None
    color: str
    hidden: bool

class GroupEntryModel(BaseModel):
    user_id: int
    group_id: int
    group: GroupModel
