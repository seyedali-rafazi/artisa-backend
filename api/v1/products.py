"""Products Router."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from core.security import get_current_user
from models.product import Product
from models.user import User
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from schemas.response import success_response, error_response

router = APIRouter()


import re

def build_persian_regex(term: str) -> str:
    """Build a flexible regex pattern matching Persian and Arabic character variants."""
    escaped = re.escape(term.strip())
    escaped = escaped.replace("ی", "[یي]").replace("ي", "[یي]")
    escaped = escaped.replace("ک", "[کك]").replace("ك", "[کك]")
    escaped = escaped.replace("آ", "[آاأإ]").replace("ا", "[آاأإ]").replace("أ", "[آاأإ]").replace("إ", "[آاأإ]")
    escaped = escaped.replace("ه", "[هة]").replace("ة", "[هة]")
    escaped = escaped.replace(r"\ ", r"[\s\u200c]+")
    return escaped


@router.get("", summary="Get products list with search, filter, sort and pagination")
@router.get("/", include_in_schema=False)
async def list_products(
    search: Optional[str] = Query(None, description="General search term"),
    category: Optional[str] = Query(None, description="Category filter"),
    isSpecial: Optional[bool] = Query(None, description="Filter amazing offers"),
    isBestSeller: Optional[bool] = Query(None, description="Filter best sellers"),
    minPrice: Optional[float] = Query(None, ge=0),
    maxPrice: Optional[float] = Query(None, ge=0),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by: price, rating, created_at"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Retrieve list of products with rich filtering options."""
    query_dict = {}

    if category:
        query_dict["category"] = category

    if isSpecial is not None:
        query_dict["isSpecial"] = isSpecial

    if isBestSeller is not None:
        query_dict["isBestSeller"] = isBestSeller

    if minPrice is not None or maxPrice is not None:
        price_query = {}
        if minPrice is not None:
            price_query["$gte"] = minPrice
        if maxPrice is not None:
            price_query["$lte"] = maxPrice
        query_dict["price"] = price_query

    # Search term matching name, category, or description with smart Persian regex
    if search and search.strip():
        term = search.strip()
        tokens = [t.strip() for t in term.split() if t.strip()]

        if len(tokens) <= 1:
            pat = build_persian_regex(term)
            reg = {"$regex": pat, "$options": "i"}
            query_dict["$or"] = [
                {"name": reg},
                {"nameEn": reg},
                {"category": reg},
                {"categoryEn": reg},
                {"description": reg},
                {"descriptionEn": reg},
            ]
        else:
            full_pat = build_persian_regex(term)
            full_reg = {"$regex": full_pat, "$options": "i"}

            token_filters = []
            for t in tokens:
                t_pat = build_persian_regex(t)
                t_reg = {"$regex": t_pat, "$options": "i"}
                token_filters.append({
                    "$or": [
                        {"name": t_reg},
                        {"nameEn": t_reg},
                        {"category": t_reg},
                        {"categoryEn": t_reg},
                        {"description": t_reg},
                        {"descriptionEn": t_reg},
                    ]
                })

            query_dict["$or"] = [
                {"name": full_reg},
                {"category": full_reg},
                {"description": full_reg},
                {"$and": token_filters},
            ]

    # Fetch with Beanie
    find_query = Product.find(query_dict)

    # Sorting
    if sort_by in ["price", "rating", "created_at"]:
        order_prefix = "-" if sort_order == "desc" else "+"
        find_query = find_query.sort(f"{order_prefix}{sort_by}")

    total_count = await find_query.count()
    skip = (page - 1) * limit
    products = await find_query.skip(skip).limit(limit).to_list()

    items = [
        ProductResponse(
            id=str(p.id),
            name=p.name,
            nameEn=p.nameEn,
            price=p.price,
            oldPrice=p.oldPrice,
            image=p.image,
            category=p.category,
            categoryEn=p.categoryEn,
            rating=p.rating,
            isSpecial=p.isSpecial,
            isBestSeller=p.isBestSeller,
            description=p.description,
            descriptionEn=p.descriptionEn,
            specifications=p.specifications or {},
        ).model_dump()
        for p in products
    ]

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    return success_response(
        data={
            "items": items,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
        message="لیست محصولات با موفقیت دریافت شد",
    )


@router.get("/{product_id}", summary="Get product details by ID")
async def get_product_by_id(product_id: str):
    """Fetch single product by MongoDB ID or string ID."""
    product = None
    try:
        from beanie import PydanticObjectId

        product = await Product.get(PydanticObjectId(product_id))
    except Exception:
        # Fallback search by id string
        pass

    if not product:
        product = await Product.find_one({"_id": product_id})

    if not product:
        return error_response(
            message="محصول مورد نظر یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    data = ProductResponse(
        id=str(product.id),
        name=product.name,
        nameEn=product.nameEn,
        price=product.price,
        oldPrice=product.oldPrice,
        image=product.image,
        category=product.category,
        categoryEn=product.categoryEn,
        rating=product.rating,
        isSpecial=product.isSpecial,
        isBestSeller=product.isBestSeller,
        description=product.description,
        descriptionEn=product.descriptionEn,
        specifications=product.specifications or {},
    ).model_dump()

    return success_response(data=data, message="اطلاعات محصول دریافت شد")


@router.post("", summary="Create a new product (Admin)")
@router.post("/", include_in_schema=False)
async def create_product(
    payload: ProductCreate, current_user: User = Depends(get_current_user)
):
    """Create a new product."""
    product = Product(
        name=payload.name,
        nameEn=payload.nameEn,
        price=payload.price,
        oldPrice=payload.oldPrice,
        image=payload.image,
        category=payload.category,
        categoryEn=payload.categoryEn,
        rating=payload.rating,
        isSpecial=payload.isSpecial,
        isBestSeller=payload.isBestSeller,
        description=payload.description,
        descriptionEn=payload.descriptionEn,
        specifications=payload.specifications,
    )
    await product.insert()

    data = ProductResponse(
        id=str(product.id),
        name=product.name,
        nameEn=product.nameEn,
        price=product.price,
        oldPrice=product.oldPrice,
        image=product.image,
        category=product.category,
        categoryEn=product.categoryEn,
        rating=product.rating,
        isSpecial=product.isSpecial,
        isBestSeller=product.isBestSeller,
        description=product.description,
        descriptionEn=product.descriptionEn,
        specifications=product.specifications or {},
    ).model_dump()

    return success_response(
        data=data,
        message="محصول جدید با موفقیت ایجاد گردید",
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/{product_id}", summary="Update product")
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update existing product details and clean up replaced Blob images."""
    from services.image_upload import cleanup_replaced_urls

    product = None
    try:
        from beanie import PydanticObjectId

        product = await Product.get(PydanticObjectId(product_id))
    except Exception:
        pass

    if not product:
        return error_response(
            message="محصول یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    previous_urls = [product.image, *(getattr(product, "gallery", None) or [])]
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(product, field, val)

    await product.save()

    next_urls = [product.image, *(getattr(product, "gallery", None) or [])]
    await cleanup_replaced_urls(previous_urls=previous_urls, next_urls=next_urls)

    data = ProductResponse(
        id=str(product.id),
        name=product.name,
        nameEn=product.nameEn,
        price=product.price,
        oldPrice=product.oldPrice,
        image=product.image,
        category=product.category,
        categoryEn=product.categoryEn,
        rating=product.rating,
        isSpecial=product.isSpecial,
        isBestSeller=product.isBestSeller,
        description=product.description,
        descriptionEn=product.descriptionEn,
        specifications=product.specifications or {},
    ).model_dump()

    return success_response(data=data, message="محصول با موفقیت بروزرسانی شد")


@router.delete("/{product_id}", summary="Delete product")
async def delete_product(
    product_id: str, current_user: User = Depends(get_current_user)
):
    """Delete product by ID and remove associated Blob images when present."""
    from services.blob_storage import delete_file

    product = None
    try:
        from beanie import PydanticObjectId

        product = await Product.get(PydanticObjectId(product_id))
    except Exception:
        pass

    if not product:
        return error_response(
            message="محصول یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    image_urls = [product.image, *(getattr(product, "gallery", None) or [])]
    await product.delete()
    # Blob deletion is best-effort; missing objects must not block deletion
    await delete_file(image_urls)
    return success_response(message="محصول با موفقیت حذف شد")
