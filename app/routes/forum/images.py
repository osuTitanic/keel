
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from app.common.config import config_instance as config
from app.common.database import screenshots
from app.security import require_login
from app.utils import requires

from PIL import Image, UnidentifiedImageError
from hashlib import md5
from io import BytesIO
from typing import IO

router = APIRouter()

IMAGE_FORMATS = ("JPEG", "PNG", "GIF", "WEBP", "BMP")
IMAGE_SIZE_MAX = 4 * 1024 * 1024

@router.post("/images", dependencies=[require_login])
@requires("forum.posts.create")
def upload_image(request: Request, input: UploadFile = File(...)) -> dict:
    """Upload an image to screenshot storage"""
    content = input.file.read(IMAGE_SIZE_MAX + 1)

    if len(content) > IMAGE_SIZE_MAX:
        raise HTTPException(413, "Images must be 4 MiB or smaller")

    if error := validate_image(request, BytesIO(content)):
        raise HTTPException(400, error)

    screenshot = screenshots.create(
        user_id=request.user.id,
        hidden=False,
        session=request.state.db
    )
    if not request.state.storage.save(screenshot.id, content, "screenshots"):
        request.state.db.rollback()
        raise HTTPException(500, "Failed to store image")

    date_string = screenshot.created_at.strftime("%Y-%m-%d %H:%M:%S")
    checksum = md5(date_string.encode()).hexdigest()
    request.state.db.commit()

    return {"url": f"{config.DEFAULT_OSU_BASEURL}/ss/{screenshot.id}/{checksum}"}

def validate_image(request: Request, content: IO[bytes]) -> str | None:
    try:
        with Image.open(content) as image:
            if image.format not in IMAGE_FORMATS:
                return "Unsupported image format"
            image.verify()
    except Exception as e:
        request.state.logger.error(f"Failed to verify image: {e}")
        return "Invalid image"
