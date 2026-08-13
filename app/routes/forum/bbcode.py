
from fastapi import Response, APIRouter, Request, Body
from fastapi.responses import HTMLResponse
from app.models import BBCodeRenderRequest
from app.common.database import users
from app.common import bbcode
from .smileys import normalize_smileys

router = APIRouter()

@router.post("/bbcode", response_class=HTMLResponse)
def render_bbcode(request: Request, data: BBCodeRenderRequest = Body(...)):
    input_text = (
        normalize_smileys(data.input) if data.enable_smilies else
        data.input
    )
    return Response(
        bbcode.render_html(
            input_text,
            resolve_user_id=lambda username: users.fetch_user_id(
                username,
                request.state.db
            )
        ),
        status_code=200,
        media_type='text/html'
    )
