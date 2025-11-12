
from pydantic import BaseModel
from datetime import datetime
from typing import Dict

class BitviewVideoModel(BaseModel):
    url: str
    file_url: str
    title: str
    uploaded_on: datetime

BitviewVideoListing = Dict[str, BitviewVideoModel]
