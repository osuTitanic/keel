
from fastapi import APIRouter, Request
from typing import List

from app.common.database import releases
from app.models import ClientModel

router = APIRouter()

@router.get("/", response_model=List[ClientModel])
def get_client_releases(request: Request) -> List[ClientModel]:
    return [
        ClientModel.model_validate(client, from_attributes=True)
        for client in releases.fetch_all(request.state.db)
    ]
