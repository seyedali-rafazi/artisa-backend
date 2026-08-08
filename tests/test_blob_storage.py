"""Unit tests for Blob storage helpers (mocked HTTP)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services import blob_storage  # noqa: E402


@pytest.mark.asyncio
async def test_upload_image_uses_rest_api(monkeypatch):
    monkeypatch.setattr(
        blob_storage.settings,
        "BLOB_READ_WRITE_TOKEN",
        "vercel_blob_rw_store_testtoken",
    )
    monkeypatch.setattr(blob_storage.settings, "BLOB_STORE_ID", "store_testid")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "url": "https://testid.public.blob.vercel-storage.com/products/abc.webp",
        "pathname": "products/abc.webp",
        "contentType": "image/webp",
        "downloadUrl": "https://testid.public.blob.vercel-storage.com/products/abc.webp?download=1",
    }

    with patch("services.blob_storage.requests.put", return_value=mock_response) as put_mock:
        result = await blob_storage.upload_image(
            b"webp-bytes",
            content_type="image/webp",
            pathname="products/abc.webp",
        )

    assert result.url.endswith("products/abc.webp")
    assert result.pathname == "products/abc.webp"
    put_mock.assert_called_once()
    _, kwargs = put_mock.call_args
    assert kwargs["headers"]["x-vercel-blob-access"] == "public"
    assert kwargs["headers"]["x-content-type"] == "image/webp"


@pytest.mark.asyncio
async def test_delete_file_ignores_non_blob_urls(monkeypatch):
    called = {"value": False}

    def fail_if_called(*args, **kwargs):
        called["value"] = True

    monkeypatch.setattr(blob_storage, "_delete_sync", fail_if_called)
    await blob_storage.delete_file("https://artisa-backend.vercel.app/uploads/x.webp")
    assert called["value"] is False
