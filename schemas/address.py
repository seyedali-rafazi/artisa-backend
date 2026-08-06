"""Address Pydantic Schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    title: str = Field(..., min_length=1)
    fullName: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=5)
    province: str
    city: str
    postalCode: str
    addressLine: str
    isDefault: bool = False


class AddressUpdate(BaseModel):
    title: Optional[str] = None
    fullName: Optional[str] = None
    phone: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    postalCode: Optional[str] = None
    addressLine: Optional[str] = None
    isDefault: Optional[bool] = None


class AddressResponse(BaseModel):
    id: str
    title: str
    fullName: str
    phone: str
    province: str
    city: str
    postalCode: str
    addressLine: str
    isDefault: bool
