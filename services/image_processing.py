"""Image validation and optimization for product uploads."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Optional, Set

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    Image = None
    class UnidentifiedImageError(Exception):
        pass

logger = logging.getLogger(__name__)

# Production defaults for product imagery
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_DIMENSION = 2000
WEBP_QUALITY = 85

ALLOWED_CONTENT_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}

FORMAT_TO_CONTENT_TYPE = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


class ImageProcessingError(Exception):
    """Client-safe image validation / processing failure."""

    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ProcessedImage:
    """Result of validating and optimizing an uploaded image."""

    data: bytes
    content_type: str
    extension: str
    width: int
    height: int
    original_size: int
    optimized_size: int


def _normalize_content_type(content_type: Optional[str]) -> str:
    if not content_type:
        return ""
    return content_type.split(";")[0].strip().lower()


def validate_and_optimize_image(
    raw_bytes: bytes,
    *,
    declared_content_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> ProcessedImage:
    """
    Validate image bytes and produce an optimized WebP payload.

    Raises ImageProcessingError with a client-safe Persian message on failure.
    """
    if not raw_bytes:
        raise ImageProcessingError("فایل تصویری خالی است")

    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise ImageProcessingError("حجم تصویر نباید بیشتر از ۵ مگابایت باشد")

    declared = _normalize_content_type(declared_content_type)
    if declared and declared not in ALLOWED_CONTENT_TYPES:
        raise ImageProcessingError(
            "فرمت تصویر پشتیبانی نمی‌شود. فرمت‌های مجاز: JPEG, PNG, WEBP"
        )

    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ImageProcessingError(
                "پسوند فایل تصویری مجاز نیست. پسوندهای مجاز: .jpg, .jpeg, .png, .webp"
            )

    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img.load()  # Force decode to catch truncated/corrupt files
            detected_format = (img.format or "").upper()

            if detected_format not in FORMAT_TO_CONTENT_TYPE:
                raise ImageProcessingError("محتوای فایل یک تصویر معتبر نیست")

            if img.mode in ("P", "LA"):
                img = img.convert("RGBA")
            elif img.mode == "CMYK":
                img = img.convert("RGB")
            elif img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGB")

            width, height = img.size
            if max(width, height) > MAX_DIMENSION:
                img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
                width, height = img.size

            output = io.BytesIO()
            save_kwargs = {
                "format": "WEBP",
                "quality": WEBP_QUALITY,
                "method": 4,
            }
            if img.mode == "RGBA":
                img.save(output, **save_kwargs)
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output, **save_kwargs)

            optimized = output.getvalue()
    except ImageProcessingError:
        raise
    except UnidentifiedImageError as exc:
        raise ImageProcessingError(
            "فایل بارگذاری‌شده یک تصویر معتبر نیست"
        ) from exc
    except OSError as exc:
        logger.warning("Image processing failed: %s", exc)
        raise ImageProcessingError(
            "پردازش تصویر با خطا مواجه شد. لطفاً فایل دیگری امتحان کنید"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected image processing error")
        raise ImageProcessingError("پردازش تصویر با خطا مواجه شد") from exc

    return ProcessedImage(
        data=optimized,
        content_type="image/webp",
        extension=".webp",
        width=width,
        height=height,
        original_size=len(raw_bytes),
        optimized_size=len(optimized),
    )
