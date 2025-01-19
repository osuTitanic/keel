
from fastapi import APIRouter
from zipfile import ZipFile
from io import BytesIO

router = APIRouter()

def remove_video_from_zip(osz: bytes) -> bytes:
    video_extensions = [
        ".wmv", ".flv", ".mp4", ".avi", ".m4v"
    ]

    with ZipFile(BytesIO(osz), 'r') as zip_file:
        files_to_keep = [
            item for item in zip_file.namelist()
            if not any(item.lower().endswith(ext) for ext in video_extensions)
        ]

        output = BytesIO()

        with ZipFile(output, 'w') as output_zip:
            for file in files_to_keep:
                output_zip.writestr(file, zip_file.read(file))

        return output.getvalue()
