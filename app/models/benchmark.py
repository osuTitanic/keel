
from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum

from .user import UserModelCompact

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
    renderer: str
    resolution: str | None = None
    fullscreen: bool | None = None
    letterboxing: bool | None = None
    cpu: str | None = None
    cores: int | None = None
    threads: int | None = None
    gpu: str | None = None
    ram: int | None = None
    os: str | None = None
    motherboard_manufacturer: str | None = None
    motherboard: str | None = None

    @field_validator('renderer', mode='before')
    def validate_renderer(cls, value, field):
        if not isinstance(value, str) or len(value) <= 0:
            raise ValueError("Renderer must be a string")

        if len(value) > 12:
            raise ValueError("Renderer must be a string of a maximum of 12 characters")

        return value

    @field_validator('resolution', mode='before')
    def validate_resolution(cls, value):
        if value is None:
            return value

        if not isinstance(value, str) or len(value) <= 0 or len(value) > 32:
            raise ValueError("Resolution must be a valid string")

        parts = value.lower().split('x')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError("Resolution must use WIDTHxHEIGHT format")

        return value

    @field_validator('cores', 'threads', mode='before')
    def validate_cores_and_threads(cls, value, field):
        if value is None:
            return value

        if not isinstance(value, int) or value <= 0:
            raise ValueError("Cores/Threads must be positive integers")

        return value

    @field_validator('ram', mode='before')
    def validate_ram(cls, value):
        if value is None:
            return value

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
