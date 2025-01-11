
from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from typing import List

class Client(BaseModel):
    name: str
    description: str
    category: str
    known_bugs: str | None
    supported: bool
    recommended: bool
    preview: bool
    downloads: List[str]
    hashes: List[dict]
    screenshots: List[dict]
    actions: List[dict]
    created_at: datetime
