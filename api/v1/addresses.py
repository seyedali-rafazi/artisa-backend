"""Addresses Router."""

from fastapi import APIRouter, Depends, status

from core.security import get_current_user
from models.address import Address
from models.user import User
from schemas.address import AddressCreate, AddressUpdate, AddressResponse
from schemas.response import success_response, error_response

router = APIRouter()


@router.get("", summary="Get user saved addresses")
@router.get("/", include_in_schema=False)
async def list_addresses(current_user: User = Depends(get_current_user)):
    """Fetch all saved addresses for current user."""
    addresses = await Address.find(Address.userId == str(current_user.id)).to_list()

    items = [
        AddressResponse(
            id=str(a.id),
            title=a.title,
            fullName=a.fullName,
            phone=a.phone,
            province=a.province,
            city=a.city,
            postalCode=a.postalCode,
            addressLine=a.addressLine,
            isDefault=a.isDefault,
        ).model_dump()
        for a in addresses
    ]

    return success_response(data=items, message="لیست آدرس‌ها دریافت شد")


@router.post("", summary="Save a new address")
@router.post("/", include_in_schema=False)
async def create_address(
    payload: AddressCreate, current_user: User = Depends(get_current_user)
):
    """Create and save new address."""
    user_id = str(current_user.id)

    # If isDefault, unmark other addresses
    if payload.isDefault:
        existing_defaults = await Address.find(
            Address.userId == user_id, Address.isDefault == True
        ).to_list()
        for addr in existing_defaults:
            addr.isDefault = False
            await addr.save()

    address = Address(
        userId=user_id,
        title=payload.title,
        fullName=payload.fullName,
        phone=payload.phone,
        province=payload.province,
        city=payload.city,
        postalCode=payload.postalCode,
        addressLine=payload.addressLine,
        isDefault=payload.isDefault,
    )
    await address.insert()

    data = AddressResponse(
        id=str(address.id),
        title=address.title,
        fullName=address.fullName,
        phone=address.phone,
        province=address.province,
        city=address.city,
        postalCode=address.postalCode,
        addressLine=address.addressLine,
        isDefault=address.isDefault,
    ).model_dump()

    return success_response(
        data=data,
        message="آدرس جدید با موفقیت اضافه شد",
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/{address_id}", summary="Update saved address")
async def update_address(
    address_id: str,
    payload: AddressUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update existing address."""
    user_id = str(current_user.id)
    address = None
    try:
        from beanie import PydanticObjectId

        address = await Address.get(PydanticObjectId(address_id))
    except Exception:
        pass

    if not address or address.userId != user_id:
        return error_response(
            message="آدرس مورد نظر یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    if payload.isDefault:
        existing_defaults = await Address.find(
            Address.userId == user_id, Address.isDefault == True
        ).to_list()
        for a in existing_defaults:
            if str(a.id) != address_id:
                a.isDefault = False
                await a.save()

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(address, field, val)

    await address.save()

    data = AddressResponse(
        id=str(address.id),
        title=address.title,
        fullName=address.fullName,
        phone=address.phone,
        province=address.province,
        city=address.city,
        postalCode=address.postalCode,
        addressLine=address.addressLine,
        isDefault=address.isDefault,
    ).model_dump()

    return success_response(data=data, message="آدرس با موفقیت بروزرسانی شد")


@router.delete("/{address_id}", summary="Delete address")
async def delete_address(
    address_id: str, current_user: User = Depends(get_current_user)
):
    """Delete address by ID."""
    user_id = str(current_user.id)
    address = None
    try:
        from beanie import PydanticObjectId

        address = await Address.get(PydanticObjectId(address_id))
    except Exception:
        pass

    if not address or address.userId != user_id:
        return error_response(
            message="آدرس یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    await address.delete()
    return success_response(message="آدرس با موفقیت حذف گردید")


@router.put("/{address_id}/default", summary="Set address as default")
async def set_default_address(
    address_id: str, current_user: User = Depends(get_current_user)
):
    """Mark an address as default."""
    user_id = str(current_user.id)
    all_addresses = await Address.find(Address.userId == user_id).to_list()

    target = None
    for a in all_addresses:
        if str(a.id) == address_id:
            target = a
            a.isDefault = True
        else:
            a.isDefault = False
        await a.save()

    if not target:
        return error_response(
            message="آدرس مورد نظر یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    return success_response(message="آدرس پیش‌فرض با موفقیت تغییر یافت")
