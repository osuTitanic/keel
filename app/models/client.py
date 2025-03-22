
from pydantic import BaseModel
from datetime import datetime
from typing import List

class ClientHashModel(BaseModel):
    file: str
    md5: List[str]

class ClientModel(BaseModel):
    name: str
    description: str
    category: str
    known_bugs: str | None
    supported: bool
    preview: bool
    downloads: List[str]
    screenshots: List[str]
    hashes: List[ClientHashModel]
    created_at: datetime

class ClientUploadRequest(BaseModel):
    name: str
    description: str
    category: str
    downloads: List[str]
    screenshots: List[str]
    hashes: List[ClientHashModel]
