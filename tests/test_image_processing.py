"""Unit tests for image processing and Blob URL helpers."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from PIL import Image

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.blob_storage import is_blob_url  # noqa: E402
from services.image_processing import (  # noqa: E402
    ImageProcessingError,
    validate_and_optimize_image,
)


def _make_image_bytes(fmt: str = "JPEG", size=(400, 300), color=(200, 100, 50)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_optimize_jpeg_to_webp():
    raw = _make_image_bytes("JPEG")
    result = validate_and_optimize_image(
        raw, declared_content_type="image/jpeg", filename="photo.jpg"
    )
    assert result.content_type == "image/webp"
    assert result.extension == ".webp"
    assert result.optimized_size > 0
    assert result.width == 400
    assert result.height == 300


def test_optimize_png_to_webp():
    raw = _make_image_bytes("PNG")
    result = validate_and_optimize_image(
        raw, declared_content_type="image/png", filename="photo.png"
    )
    assert result.content_type == "image/webp"
    assert result.width == 400


def test_reject_oversized_file():
    raw = b"x" * (5 * 1024 * 1024 + 1)
    with pytest.raises(ImageProcessingError):
        validate_and_optimize_image(raw, declared_content_type="image/jpeg")


def test_reject_invalid_bytes():
    with pytest.raises(ImageProcessingError):
        validate_and_optimize_image(
            b"not-an-image", declared_content_type="image/jpeg", filename="x.jpg"
        )


def test_reject_unsupported_mime():
    raw = _make_image_bytes("JPEG")
    with pytest.raises(ImageProcessingError):
        validate_and_optimize_image(raw, declared_content_type="image/gif")


def test_does_not_upscale_small_images():
    raw = _make_image_bytes("JPEG", size=(120, 80))
    result = validate_and_optimize_image(raw, declared_content_type="image/jpeg")
    assert result.width == 120
    assert result.height == 80


def test_downscales_large_images():
    raw = _make_image_bytes("JPEG", size=(4000, 3000))
    result = validate_and_optimize_image(raw, declared_content_type="image/jpeg")
    assert max(result.width, result.height) <= 2000


def test_is_blob_url():
    assert is_blob_url(
        "https://abc123.public.blob.vercel-storage.com/products/x.webp"
    )
    assert not is_blob_url("https://artisa-backend.vercel.app/uploads/x.webp")
    assert not is_blob_url("/uploads/x.webp")
    assert not is_blob_url(None)
