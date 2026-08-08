"""High-level image upload orchestration: validate → optimize → Blob."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, UploadFile

from services.blob_storage import (
    BlobConfigError,
    BlobStorageError,
    BlobUploadResult,
    build_product_pathname,
    delete_file,
    upload_image,
)
from services.image_processing import ImageProcessingError, validate_and_optimize_image


@dataclass(frozen=True)
class UploadedImage:
    """Public upload result kept compatible with existing API clients."""

    url: str
    pathname: str
    filename: str
    content_type: str
    width: int
    height: int
    original_size: int
    optimized_size: int


async def process_and_upload_image(
    file: UploadFile,
    *,
    folder: str = "products",
) -> UploadedImage:
    """
    Read an uploaded file, validate/optimize it, and store it in Vercel Blob.
    """
    raw_bytes = await file.read()
    try:
        processed = validate_and_optimize_image(
            raw_bytes,
            declared_content_type=file.content_type,
            filename=file.filename,
        )
    except ImageProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    pathname = build_product_pathname(processed.extension)
    if folder and folder != "products":
        pathname = f"{folder}/{pathname.split('/', 1)[-1]}"

    try:
        blob: BlobUploadResult = await upload_image(
            processed.data,
            content_type=processed.content_type,
            pathname=pathname,
        )
    except (BlobConfigError, BlobStorageError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    filename = blob.pathname.rsplit("/", 1)[-1]
    return UploadedImage(
        url=blob.url,
        pathname=blob.pathname,
        filename=filename,
        content_type=blob.content_type,
        width=processed.width,
        height=processed.height,
        original_size=processed.original_size,
        optimized_size=processed.optimized_size,
    )


async def cleanup_replaced_urls(
    *,
    previous_urls: list[str],
    next_urls: list[str],
) -> None:
    """Delete Blob URLs that were removed during a product update."""
    previous_set = {u for u in previous_urls if u}
    next_set = {u for u in next_urls if u}
    removed = list(previous_set - next_set)
    if removed:
        await delete_file(removed)


__all__ = [
    "UploadedImage",
    "process_and_upload_image",
    "cleanup_replaced_urls",
    "delete_file",
]
