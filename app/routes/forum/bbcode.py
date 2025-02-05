
from fastapi import Response, APIRouter, Request, Body
from app.models import BBCodeRenderRequest
from app import bbcode

router = APIRouter()

@router.post("/bbcode")
def render_bbcode(request: Request, data: BBCodeRenderRequest = Body(...)):
    return Response(
        bbcode.render_html(data.input),
        status_code=200,
        media_type='text/html'
    )
