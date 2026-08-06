"""Standard API Response helper and schemas for Artisa API."""

from typing import Any, Generic, List, Optional, TypeVar
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard unified response wrapper."""

    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[Any]] = None


def success_response(
    data: Any = None, message: str = "عملیات با موفقیت انجام شد", status_code: int = 200
) -> JSONResponse:
    """Return a standard success response."""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "success": True,
                "message": message,
                "data": data,
            }
        ),
    )


def error_response(
    message: str = "خطایی رخ داده است",
    errors: Optional[List[Any]] = None,
    status_code: int = 400,
) -> JSONResponse:
    """Return a standard error response."""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "success": False,
                "message": message,
                "errors": errors or [],
            }
        ),
    )
