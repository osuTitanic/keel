
from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum

from .user import UserModelCompact

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
    user: UserModelCompact

class BenchmarkHardware(BaseModel):
    renderer: Renderer
    cpu: str
    cores: int
    threads: int
    gpu: str
    ram: int
    os: str
    motherboard_manufacturer: str
    motherboard: str

    @field_validator('cores', 'threads', mode='before')
    def validate_cores_and_threads(cls, value, field):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field.name} must be a positive integer")
        return value
    
    @field_validator('ram', mode='before')
    def validate_ram(cls, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("RAM must be a non-negative integer")
        return value

class BenchmarkSubmissionRequest(BaseModel):
    smoothness: float
    framerate: int
    raw_score: int
    client: str
    hardware: BenchmarkHardware

    @property
    def grade(self) -> str:
        if self.smoothness >= 100: return 'SS'
        elif self.smoothness > 95: return 'S'
        elif self.smoothness > 90: return 'A'
        elif self.smoothness > 80: return 'B'
        elif self.smoothness > 70: return 'C'
        else: return 'D'

    @field_validator('framerate', mode='before')
    def validate_framerate(cls, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Framerate must be a positive integer")
        if value > 1_000_000:
            raise ValueError("Framerate is too high")
        return value

    @field_validator('raw_score', mode='before')
    def validate_raw_score(cls, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Raw score must be a positive integer")
        if value > 1_000_000_000:
            raise ValueError("Raw score is too high")
        return value

    @field_validator('smoothness', mode='before')
    def validate_smoothness(cls, value):
        if not isinstance(value, float) or value < 0 or value > 100:
            raise ValueError("Smoothness must be a float between 0 and 100")
        return value
