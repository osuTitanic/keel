
from fastapi import HTTPException, APIRouter, Request, Form
from fastapi.responses import JSONResponse
from app.models.kofi import KofiWebhookData
from config import KOFI_VERIFICATION_TOKEN

router = APIRouter()

@router.post("/callback")
def kofi_donation_webhook(
    request: Request,
    data: KofiWebhookData = Form(...)
) -> JSONResponse:
    if data.verification_token != KOFI_VERIFICATION_TOKEN:
        raise HTTPException(403, detail="Invalid verification token")

    request.state.logger.info(f"Kofi donation received: {data}")
    return JSONResponse({'success': True}, status_code=200)
