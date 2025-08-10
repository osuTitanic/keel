
from fastapi import HTTPException, APIRouter, Request, Form
from fastapi.responses import JSONResponse
from app.models.kofi import KofiWebhookData

import config
import json

router = APIRouter()

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

    request.state.logger.info(f"Kofi donation received: {data}")
    return JSONResponse({'success': True}, status_code=200)
