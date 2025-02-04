
from app.common.constants import Playstyle
from pydantic import BaseModel, field_validator

class PlaystyleResponseModel(BaseModel):
    playstyle: int

class PlaystyleRequestModel(BaseModel):
    playstyle: str

    @field_validator('playstyle')
    def validate_playstyle(cls, value):
        if value not in Playstyle.__members__:
            raise ValueError('Invalid playstyle')

        return value
