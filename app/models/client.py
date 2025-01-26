
from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from typing import List

class ClientHashModel(BaseModel):
    md5: List[str]
    file: str

class ClientScreenshotModel(BaseModel):
    src: str
    width: str
    height: str

class ClientModel(BaseModel):
    name: str
    description: str
    category: str
    known_bugs: str | None
    supported: bool
    recommended: bool
    preview: bool
    downloads: List[str]
    hashes: List[ClientHashModel]
    screenshots: List[ClientScreenshotModel]
    created_at: datetime

class ClientUploadRequest(BaseModel):
    name: str
    description: str
    category: str
    downloads: List[str]
    hashes: List[ClientHashModel]
    screenshots: List[ClientScreenshotModel]
