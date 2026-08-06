"""File Upload Router."""

import os
import uuid
from fastapi import APIRouter, File, UploadFile, Depends, status

from core.security import get_current_user
from models.user import User
from schemas.response import success_response, error_response

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", summary="Upload image file")
@router.post("/", include_in_schema=False)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image file and return its accessible URL."""
    if not file.content_type.startswith("image/"):
        return error_response(
            message="فقط فایل‌های تصویری مجاز هستند",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)

    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    url = f"/uploads/{unique_filename}"

    return success_response(
        data={"url": url, "filename": unique_filename},
        message="تصویر با موفقیت بارگذاری شد",
        status_code=status.HTTP_201_CREATED,
    )
