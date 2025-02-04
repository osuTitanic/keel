
from pydantic import BaseModel
from datetime import datetime
from typing import List

from .user import UserModelCompact, UserModel

class IconModel(BaseModel):
    id: int
    name: str
    location: str

class PostModel(BaseModel):
    id: int
    topic_id: int
    forum_id: int
    user_id: int
    content: str
    created_at: datetime
    edit_time: datetime
    edit_count: int
    edit_locked: bool
    deleted: bool
    user: UserModel

class TopicModel(BaseModel):
    id: int
    forum_id: int
    creator_id: int
    icon_id: int | None
    title: str
    status_text: str | None
    views: int
    announcement: bool
    pinned: bool
    created_at: datetime
    last_post_at: datetime
    locked_at: datetime | None
    creator: UserModelCompact
    icon: IconModel | None

class SubforumModel(BaseModel):
    id: int
    parent_id: int | None
    created_at: datetime
    name: str
    description: str

class ForumModel(BaseModel):
    id: int
    parent_id: int | None
    created_at: datetime
    name: str
    description: str
    subforums: List[SubforumModel]
    parent: SubforumModel | None

class BookmarkModel(BaseModel):
    user: UserModelCompact
    topic: TopicModel

class SubscriptionModel(BaseModel):
    user: UserModelCompact
    topic: TopicModel

class BBCodeRenderRequest(BaseModel):
    input: str

class SubscriptionRequest(BaseModel):
    topic_id: int

class BookmarkRequest(BaseModel):
    topic_id: int
