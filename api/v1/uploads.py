"""File Upload Router — validates, optimizes, and stores images in Vercel Blob."""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status

from core.security import get_current_user
from models.user import User
from schemas.response import success_response, error_response
from services.image_upload import process_and_upload_image

router = APIRouter()


@router.post("", summary="Upload image file")
@router.post("/", include_in_schema=False)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image, optimize to WebP, store in Vercel Blob, return public URL."""
    try:
        uploaded = await process_and_upload_image(file)
    except HTTPException as exc:
        return error_response(
            message=exc.detail if isinstance(exc.detail, str) else "خطا در آپلود تصویر",
            status_code=exc.status_code,
        )

    return success_response(
        data={
            "url": uploaded.url,
            "pathname": uploaded.pathname,
            "filename": uploaded.filename,
            "content_type": uploaded.content_type,
        },
        message="تصویر با موفقیت بارگذاری شد",
        status_code=status.HTTP_201_CREATED,
    )
