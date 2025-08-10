
from fastapi import HTTPException, APIRouter, Request, Form
from fastapi.responses import JSONResponse

from app.common.database.repositories import groups, users
from app.models.kofi import KofiWebhookData
from app.common import webhooks, officer

import config
import json

router = APIRouter()
donator_group_id = 6

@router.post("/callback")
def kofi_donation_webhook(
    request: Request,
    data_encoded: str = Form(..., alias="data")
) -> JSONResponse:
    data = KofiWebhookData.model_validate_json(data_encoded)

    if request.headers.get('User-Agent') != 'Kofi.Webhooks':
        raise HTTPException(403, detail="Unauthorized")

    if data.verification_token != config.KOFI_VERIFICATION_TOKEN:
        raise HTTPException(403, detail="Invalid verification token")

    request.state.logger.info(f"Ko-Fi donation received from '{data.from_name}' ({data.url})")
    assign_donator_group(data, request)

    if not data.is_public:
        return JSONResponse({'success': True}, status_code=200)

    embed = webhooks.Embed(
        title=f"{data.from_name} supported Titanic!",
        description=data.message,
        color=0x00FF37,
        url=data.url
    )

    # Announce in events channel
    officer.event(embed=embed)

    return JSONResponse({'success': True}, status_code=200)

def assign_donator_group(data: KofiWebhookData, request: Request) -> bool:
    user = (
        users.fetch_by_email(data.email, request.state.db) or
        users.fetch_by_name_extended(data.from_name, request.state.db)
    )

    if not user:
        return False

    if user.activated:
        return False

    if groups.entry_exists(user.id, donator_group_id, request.state.db):
        return True

    groups.create_entry(
        user.id, donator_group_id,
        session=request.state.db
    )
    return True
