
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse
from app.security import require_login
from app.utils import requires
from requests import Response
from time import time

router = APIRouter()

@router.post("/images", dependencies=[require_login])
@requires("forum.posts.create")
def upload_image(request: Request, input: UploadFile = File(...)) -> dict:
    """Upload an image to imgbb.com"""
    response: Response = request.state.requests.post(
        "https://imgbb.com/json",
        files={
            "source": (input.filename, input.file.read(), input.content_type or "image"),
            "type": (None, "file"),
            "action": (None, "upload"),
            "timestamp": (None, round(time())),
            "auth_token": (None, "778d04bbb1eea95cead873eb0adb8921b24dfbc5"),
        },
        headers={
            "referer": "https://imgbb.com/",
            "accept": "application/json"
        }
    )

    return JSONResponse(
        status_code=response.status_code,
        content=response.json()
    )
