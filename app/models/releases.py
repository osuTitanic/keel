
from pydantic import BaseModel, ValidationInfo, field_validator
from datetime import datetime
from typing import List

class TitanicReleaseModel(BaseModel):
    name: str
    description: str
    category: str
    known_bugs: str | None
    supported: bool
    preview: bool
    downloads: List[str]
    screenshots: List[str]
    created_at: datetime

class ModdedReleaseModel(BaseModel):
    name: str
    description: str
    creator_id: int | None
    topic_id: int | None
    client_version: int
    client_extension: str
    created_at: datetime

class OsuChangelogModel(BaseModel):
    id: int
    text: str
    type: str
    branch: str
    author: str
    area: str | None
    created_at: datetime

class OsuReleaseModelCompact(BaseModel):
    id: int
    version: int
    subversion: int
    stream: str
    created_at: datetime

class OsuReleaseFile(BaseModel):
    id: int
    filename: str
    file_version: int
    file_hash: str
    filesize: int
    patch_id: str | None
    url_full: str
    url_patch: str | None
    timestamp: datetime

class OsuReleaseModel(OsuReleaseModelCompact):
    files: List[OsuReleaseFile]
    
    @field_validator('files', mode='before')
    @classmethod
    def resolve_files(cls, v, info: ValidationInfo) -> List[OsuReleaseFile]:
        if v:
            # Files were provided directly
            return v

        # Get from context if available
        context = info.context or {}
        files = context.get(cls.id)

        if not files:
            return []

        return [
            OsuReleaseFile.model_validate(file_object)
            for file_object in files
        ]

class OsuReleaseUploadRequest(OsuReleaseModelCompact):
    files: List[int]
