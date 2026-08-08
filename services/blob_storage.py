"""Vercel Blob storage service for product images."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence
from urllib.parse import urlparse

import requests

from core.config import settings

logger = logging.getLogger(__name__)

BLOB_API_BASE = "https://vercel.com/api/blob"
BLOB_API_VERSION = "7"
BLOB_HOST_MARKERS = (
    "blob.vercel-storage.com",
    "public.blob.vercel-storage.com",
)


class BlobStorageError(Exception):
    """Raised when a Blob operation fails for infrastructure reasons."""

    def __init__(self, message: str, *, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BlobConfigError(BlobStorageError):
    """Raised when Blob credentials are missing."""

    def __init__(self, message: str = "سرویس ذخیره‌سازی تصاویر پیکربندی نشده است"):
        super().__init__(message, status_code=503)


@dataclass(frozen=True)
class BlobUploadResult:
    """Metadata returned after a successful Blob upload."""

    url: str
    pathname: str
    content_type: str
    download_url: Optional[str] = None


def is_blob_url(url: Optional[str]) -> bool:
    """Return True if the URL points at Vercel Blob storage."""
    if not url or not isinstance(url, str):
        return False
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return any(marker in host for marker in BLOB_HOST_MARKERS)


def _require_token() -> str:
    token = (settings.BLOB_READ_WRITE_TOKEN or "").strip()
    if not token:
        raise BlobConfigError()
    return token


def _auth_headers(token: str, *, content_type: Optional[str] = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": BLOB_API_VERSION,
        "x-vercel-blob-access": "public",
    }
    store_id = (settings.BLOB_STORE_ID or "").strip()
    if store_id:
        headers["x-vercel-blob-store-id"] = (
            store_id[len("store_") :] if store_id.startswith("store_") else store_id
        )
    if content_type:
        headers["x-content-type"] = content_type
    return headers


def _put_sync(
    pathname: str,
    data: bytes,
    *,
    content_type: str,
    token: str,
) -> BlobUploadResult:
    params = {"pathname": pathname}
    headers = _auth_headers(token, content_type=content_type)
    headers["x-add-random-suffix"] = "0"

    try:
        response = requests.put(
            BLOB_API_BASE,
            params=params,
            headers=headers,
            data=data,
            timeout=60,
        )
    except requests.RequestException as exc:
        logger.error("Blob upload network error: %s", exc)
        raise BlobStorageError("Blob upload network failure") from exc

    if response.status_code >= 400:
        logger.error(
            "Blob upload failed status=%s body=%s",
            response.status_code,
            response.text[:500],
        )
        raise BlobStorageError(f"Blob upload failed ({response.status_code})")

    try:
        payload = response.json()
    except ValueError as exc:
        raise BlobStorageError("Invalid Blob upload response") from exc

    url = payload.get("url")
    returned_pathname = payload.get("pathname") or pathname
    if not url:
        raise BlobStorageError("Blob upload response missing url")

    return BlobUploadResult(
        url=url,
        pathname=returned_pathname,
        content_type=payload.get("contentType") or content_type,
        download_url=payload.get("downloadUrl"),
    )


def _delete_sync(urls: Sequence[str], *, token: str) -> None:
    if not urls:
        return

    headers = _auth_headers(token)
    headers["Content-Type"] = "application/json"

    try:
        response = requests.post(
            f"{BLOB_API_BASE}/delete",
            headers=headers,
            json={"urls": list(urls)},
            timeout=60,
        )
    except requests.RequestException as exc:
        logger.error("Blob delete network error: %s", exc)
        raise BlobStorageError("Blob delete network failure") from exc

    if response.status_code in (404, 400):
        logger.warning(
            "Blob delete soft-failed status=%s body=%s",
            response.status_code,
            response.text[:300],
        )
        return

    if response.status_code >= 400:
        logger.error(
            "Blob delete failed status=%s body=%s",
            response.status_code,
            response.text[:500],
        )
        raise BlobStorageError(f"Blob delete failed ({response.status_code})")


async def _put_via_sdk(
    pathname: str,
    data: bytes,
    *,
    content_type: str,
    token: str,
) -> Optional[BlobUploadResult]:
    """Try the official vercel SDK; return None if unavailable."""
    try:
        from vercel.blob import put_async  # type: ignore
    except ImportError:
        return None

    result = await put_async(
        pathname,
        data,
        access="public",
        content_type=content_type,
        add_random_suffix=False,
        token=token,
    )
    return BlobUploadResult(
        url=result.url,
        pathname=getattr(result, "pathname", None) or pathname,
        content_type=getattr(result, "content_type", None) or content_type,
        download_url=getattr(result, "download_url", None),
    )


async def _delete_via_sdk(urls: Sequence[str], *, token: str) -> bool:
    """Try the official vercel SDK delete; return False if unavailable."""
    try:
        from vercel.blob import delete_async  # type: ignore
    except ImportError:
        return False

    await delete_async(list(urls), token=token)
    return True


def build_product_pathname(extension: str = ".webp") -> str:
    """Generate a server-side storage key under products/."""
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"products/{uuid.uuid4().hex}{ext}"


async def upload_image(
    data: bytes,
    *,
    content_type: str = "image/webp",
    pathname: Optional[str] = None,
    folder: str = "products",
) -> BlobUploadResult:
    """
    Upload binary image data to Vercel Blob.

    Returns public URL metadata. Raises BlobStorageError / BlobConfigError.
    """
    token = _require_token()
    key = pathname or f"{folder}/{uuid.uuid4().hex}.webp"

    try:
        sdk_result = await _put_via_sdk(
            key, data, content_type=content_type, token=token
        )
        if sdk_result is not None:
            return sdk_result

        return await asyncio.to_thread(
            _put_sync, key, data, content_type=content_type, token=token
        )
    except BlobStorageError:
        raise
    except Exception as exc:
        logger.exception("Unexpected Blob upload error")
        raise BlobStorageError(
            "آپلود تصویر در فضای ذخیره‌سازی با خطا مواجه شد"
        ) from exc


async def delete_file(url_or_urls: str | Iterable[str]) -> None:
    """
    Delete one or more Blob objects by public URL.

    Silently ignores empty inputs and non-Blob URLs.
    Does not raise for missing objects; logs and continues.
    """
    if isinstance(url_or_urls, str):
        candidates: List[str] = [url_or_urls]
    else:
        candidates = [u for u in url_or_urls if u]

    urls = [u for u in candidates if is_blob_url(u)]
    if not urls:
        return

    token = (settings.BLOB_READ_WRITE_TOKEN or "").strip()
    if not token:
        logger.warning("Skipping Blob delete; BLOB_READ_WRITE_TOKEN is not configured")
        return

    try:
        used_sdk = await _delete_via_sdk(urls, token=token)
        if not used_sdk:
            await asyncio.to_thread(_delete_sync, urls, token=token)
    except Exception as exc:
        logger.warning("Blob delete soft-failed for %s: %s", urls, exc)


async def replace_image(
    *,
    new_data: bytes,
    content_type: str = "image/webp",
    old_url: Optional[str] = None,
    pathname: Optional[str] = None,
) -> BlobUploadResult:
    """
    Upload a new image first, then delete the previous Blob URL if present.

    The old image is only removed after the new upload succeeds.
    """
    uploaded = await upload_image(
        new_data, content_type=content_type, pathname=pathname
    )

    if old_url and old_url != uploaded.url:
        await delete_file(old_url)

    return uploaded
