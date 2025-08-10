
from fastapi import APIRouter, Request, Response, Form
from app.models.kofi import KofiWebhookData

router = APIRouter()

@router.post("/callback")
def kofi_donation_webhook(
    request: Request,
    data: KofiWebhookData = Form(...)
) -> Response:
    request.state.logger.info(f"Kofi donation received: {data}")
    return Response(status_code=200)
