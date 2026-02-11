
from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import datetime
from typing import List
from enum import Enum

from .user import UserModelCompact

class TopicType(str, Enum):
    Announcement = 'announcement'
    Pinned = 'pinned'

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
    user: UserModelCompact

    @field_validator('content', mode='after')
    def override_deleted_content(cls, value, info: ValidationInfo):
        if info.data.get('deleted'):
            return '[ Deleted ]'

        return value

class TopicModel(BaseModel):
    id: int
    forum_id: int
    creator_id: int
    icon_id: int | None
    title: str
    status_text: str | None
    views: int
    post_count: int
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
    topic_count: int
    post_count: int

class ForumModel(BaseModel):
    id: int
    parent_id: int | None
    created_at: datetime
    name: str
    description: str
    topic_count: int
    post_count: int
    subforums: List[SubforumModel]
    parent: SubforumModel | None

class BookmarkModel(BaseModel):
    user: UserModelCompact
    topic: TopicModel

class SubscriptionModel(BaseModel):
    user: UserModelCompact
    topic: TopicModel

class TopicCreateRequest(BaseModel):
    title: str
    content: str
    notify: bool = False
    icon: int | None = None
    type: TopicType | None = None

    @field_validator('title')
    def title_length(cls, value):
        if not value:
            raise ValueError('Title cannot be empty')

        return value
    
    @field_validator('content')
    def content_length(cls, value):
        if not value:
            raise ValueError('Content cannot be empty')

        return value

class TopicUpdateRequest(BaseModel):
    forum_id: int | None = None
    title: str | None = None
    icon: int | None = None
    type: TopicType | None = None
    status_text: str | None = None
    lock_topic: bool | None = None

    @field_validator('title')
    def title_length(cls, value):
        if value is not None and not value:
            raise ValueError('Title cannot be empty')

        return value

class PostCreateRequest(BaseModel):
    content: str
    notify: bool = False
    icon_update: int | None = None

    @field_validator('content')
    def content_length(cls, value):
        if not value:
            raise ValueError('Content cannot be empty')

        return value

class PostUpdateRequest(BaseModel):
    content: str
    lock: bool = False

    @field_validator('content')
    def content_length(cls, value):
        if not value:
            raise ValueError('Content cannot be empty')

        return value

class ForumHideRequest(BaseModel):
    hidden: bool

class BBCodeRenderRequest(BaseModel):
    input: str

class SubscriptionRequest(BaseModel):
    topic_id: int

class BookmarkRequest(BaseModel):
    topic_id: int
