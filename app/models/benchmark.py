
from __future__ import annotations
from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum

from .user import UserModel

class Renderer(str, Enum):
    opengl = 'OpenGL'
    directx = 'DirectX'

class BenchmarkModel(BaseModel):
    id: int
    smoothness: float
    framerate: int
    score: int
    grade: str
    created_at: datetime
    client: str
    hardware: dict | None
    user: UserModel

class BenchmarkSubmissionRequest(BaseModel):
    renderer: Renderer
    cpu: str
    cores: int
    threads: int
    gpu: str
    ram: int
    os: str
    motherboard_manufacturer: str
    motherboard: str

    @field_validator('cores', 'threads')
    def validate_cores_and_threads(cls, value, field):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field.name} must be a positive integer")
        return value
    
    @field_validator('ram')
    def validate_ram(cls, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("RAM must be a non-negative integer")
        return value

