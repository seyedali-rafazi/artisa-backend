"""Special Offer Business Logic and Service Layer."""

import math
from typing import Dict, List, Optional, Tuple
from bson import ObjectId
from beanie import PydanticObjectId
from fastapi import HTTPException, Request, status

from core.timezone import now_utc, to_utc, format_tehran_iso, get_offer_status
from models.user import User
from models.product import Product
from models.special_offer import SpecialOffer
from schemas.special_offer import (
    SpecialOfferCreate,
    SpecialOfferUpdate,
    SpecialOfferResponse,
    SpecialOfferProductSummary,
)
from services.audit_service import AuditLogService


class SpecialOfferService:
    """Service class for Special Offers lifecycle and administrative management."""

    @staticmethod
    def _parse_object_id(id_str: str) -> Optional[ObjectId]:
        """Safely convert a string to BSON ObjectId."""
        try:
            return ObjectId(id_str)
        except Exception:
            return None

    @classmethod
    async def _fetch_and_map_products(cls, product_ids: List[str]) -> Dict[str, SpecialOfferProductSummary]:
        """Batch fetch products by IDs and return a lookup dictionary."""
        if not product_ids:
            return {}

        object_ids = [cls._parse_object_id(pid) for pid in product_ids if cls._parse_object_id(pid) is not None]
        string_ids = [pid for pid in product_ids if cls._parse_object_id(pid) is None]

        query = {"$or": []}
        if object_ids:
            query["$or"].append({"_id": {"$in": object_ids}})
        if string_ids:
            query["$or"].append({"_id": {"$in": string_ids}})

        if not query["$or"]:
            return {}

        products = await Product.find(query).to_list()
        result: Dict[str, SpecialOfferProductSummary] = {}
        for p in products:
            pid_str = str(p.id)
            result[pid_str] = SpecialOfferProductSummary(
                id=pid_str,
                name=p.name,
                nameEn=getattr(p, "nameEn", "") or "",
                price=p.price,
                oldPrice=getattr(p, "oldPrice", None),
                image=p.image,
                category=p.category,
                categoryEn=getattr(p, "categoryEn", "") or "",
                rating=getattr(p, "rating", 5.0) or 5.0,
                stock_quantity=getattr(p, "stock_quantity", 100) or 0,
                status=getattr(p, "status", "published") or "published",
            )
        return result

    @classmethod
    async def _validate_products_exist(cls, product_ids: List[str]) -> List[str]:
        """Ensure all product IDs exist in database and return valid IDs list."""
        if not product_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="حداقل یک محصول باید انتخاب شود",
            )

        products_map = await cls._fetch_and_map_products(product_ids)
        missing = [pid for pid in product_ids if pid not in products_map]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"برخی از محصولات انتخاب شده یافت نشدند: {', '.join(missing[:3])}",
            )
        return product_ids

    @classmethod
    def _build_response(
        cls,
        offer: SpecialOffer,
        products_map: Optional[Dict[str, SpecialOfferProductSummary]] = None,
    ) -> SpecialOfferResponse:
        """Construct a standardized SpecialOfferResponse object."""
        products_list: List[SpecialOfferProductSummary] = []
        if products_map:
            for pid in offer.product_ids:
                if pid in products_map:
                    products_list.append(products_map[pid])

        return SpecialOfferResponse(
            id=str(offer.id),
            title=offer.title,
            description=offer.description,
            product_ids=offer.product_ids,
            products=products_list,
            start_at=offer.start_at,
            end_at=offer.end_at,
            start_at_tehran=format_tehran_iso(offer.start_at),
            end_at_tehran=format_tehran_iso(offer.end_at),
            is_active=offer.is_active,
            status=get_offer_status(offer.start_at, offer.end_at, offer.is_active),
            created_at=offer.created_at,
            updated_at=offer.updated_at,
        )

    # ─── ADMIN OPERATIONS ──────────────────────────────────────────────────

    @classmethod
    async def create_offer(
        cls,
        admin_user: User,
        payload: SpecialOfferCreate,
        request: Optional[Request] = None,
    ) -> SpecialOfferResponse:
        """Create a new Special Offer document."""
        # Validate that all selected products exist
        await cls._validate_products_exist(payload.product_ids)

        offer = SpecialOffer(
            title=payload.title,
            description=payload.description,
            product_ids=payload.product_ids,
            start_at=payload.start_at,
            end_at=payload.end_at,
            is_active=payload.is_active,
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        await offer.insert()

        # Audit log
        await AuditLogService.log_action(
            user=admin_user,
            action="CREATE_SPECIAL_OFFER",
            resource=f"special_offer_{offer.id}",
            details={
                "title": offer.title,
                "product_count": len(offer.product_ids),
                "start_at": offer.start_at.isoformat(),
                "end_at": offer.end_at.isoformat(),
                "is_active": offer.is_active,
            },
            request=request,
        )

        products_map = await cls._fetch_and_map_products(offer.product_ids)
        return cls._build_response(offer, products_map)

    @classmethod
    async def update_offer(
        cls,
        admin_user: User,
        offer_id: str,
        payload: SpecialOfferUpdate,
        request: Optional[Request] = None,
    ) -> SpecialOfferResponse:
        """Update an existing Special Offer."""
        offer = None
        obj_id = cls._parse_object_id(offer_id)
        if obj_id:
            offer = await SpecialOffer.get(PydanticObjectId(obj_id))
        if not offer:
            offer = await SpecialOffer.find_one({"_id": offer_id})

        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="پیشنهاد ویژه مورد نظر یافت نشد",
            )

        # Validate and apply product_ids
        if payload.product_ids is not None:
            await cls._validate_products_exist(payload.product_ids)
            offer.product_ids = payload.product_ids

        # Validate date consistency
        new_start = to_utc(payload.start_at) if payload.start_at is not None else offer.start_at
        new_end = to_utc(payload.end_at) if payload.end_at is not None else offer.end_at

        if new_end <= new_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="زمان پایان پیشنهاد باید بعد از زمان شروع باشد",
            )

        offer.start_at = new_start
        offer.end_at = new_end

        if payload.title is not None:
            offer.title = payload.title
        if payload.description is not None:
            offer.description = payload.description
        if payload.is_active is not None:
            offer.is_active = payload.is_active

        offer.updated_at = now_utc()
        await offer.save()

        # Audit log
        await AuditLogService.log_action(
            user=admin_user,
            action="UPDATE_SPECIAL_OFFER",
            resource=f"special_offer_{offer.id}",
            details={
                "title": offer.title,
                "product_count": len(offer.product_ids),
                "start_at": offer.start_at.isoformat(),
                "end_at": offer.end_at.isoformat(),
                "is_active": offer.is_active,
            },
            request=request,
        )

        products_map = await cls._fetch_and_map_products(offer.product_ids)
        return cls._build_response(offer, products_map)

    @classmethod
    async def toggle_active(
        cls,
        admin_user: User,
        offer_id: str,
        is_active: Optional[bool] = None,
        request: Optional[Request] = None,
    ) -> SpecialOfferResponse:
        """Toggle active state of a special offer."""
        offer = None
        obj_id = cls._parse_object_id(offer_id)
        if obj_id:
            offer = await SpecialOffer.get(PydanticObjectId(obj_id))
        if not offer:
            offer = await SpecialOffer.find_one({"_id": offer_id})

        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="پیشنهاد ویژه مورد نظر یافت نشد",
            )

        offer.is_active = is_active if is_active is not None else not offer.is_active
        offer.updated_at = now_utc()
        await offer.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="TOGGLE_SPECIAL_OFFER",
            resource=f"special_offer_{offer.id}",
            details={"is_active": offer.is_active},
            request=request,
        )

        products_map = await cls._fetch_and_map_products(offer.product_ids)
        return cls._build_response(offer, products_map)

    @classmethod
    async def delete_offer(
        cls,
        admin_user: User,
        offer_id: str,
        request: Optional[Request] = None,
    ):
        """Delete a Special Offer."""
        offer = None
        obj_id = cls._parse_object_id(offer_id)
        if obj_id:
            offer = await SpecialOffer.get(PydanticObjectId(obj_id))
        if not offer:
            offer = await SpecialOffer.find_one({"_id": offer_id})

        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="پیشنهاد ویژه مورد نظر یافت نشد",
            )

        await offer.delete()

        await AuditLogService.log_action(
            user=admin_user,
            action="DELETE_SPECIAL_OFFER",
            resource=f"special_offer_{offer_id}",
            details={"title": offer.title},
            request=request,
        )

    @classmethod
    async def get_offer_by_id(cls, offer_id: str) -> SpecialOfferResponse:
        """Get a single offer with populated products."""
        offer = None
        obj_id = cls._parse_object_id(offer_id)
        if obj_id:
            offer = await SpecialOffer.get(PydanticObjectId(obj_id))
        if not offer:
            offer = await SpecialOffer.find_one({"_id": offer_id})

        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="پیشنهاد ویژه مورد نظر یافت نشد",
            )

        products_map = await cls._fetch_and_map_products(offer.product_ids)
        return cls._build_response(offer, products_map)

    @classmethod
    async def list_admin_offers(
        cls,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[SpecialOfferResponse], int, int]:
        """List paginated special offers for admin with flexible filtering."""
        curr_utc = now_utc()
        query_dict = {}

        if search and search.strip():
            query_dict["$or"] = [
                {"title": {"$regex": search.strip(), "$options": "i"}},
                {"description": {"$regex": search.strip(), "$options": "i"}},
            ]

        if status_filter:
            sf = status_filter.strip().lower()
            if sf == "active":
                query_dict["is_active"] = True
                query_dict["start_at"] = {"$lte": curr_utc}
                query_dict["end_at"] = {"$gt": curr_utc}
            elif sf == "upcoming":
                query_dict["is_active"] = True
                query_dict["start_at"] = {"$gt": curr_utc}
            elif sf == "expired":
                query_dict["is_active"] = True
                query_dict["end_at"] = {"$lte": curr_utc}
            elif sf == "inactive":
                query_dict["is_active"] = False

        find_query = SpecialOffer.find(query_dict).sort("-created_at")
        total_count = await find_query.count()
        skip = (page - 1) * limit
        offers = await find_query.skip(skip).limit(limit).to_list()

        # Batch fetch all product IDs across all offers in this page
        all_product_ids = []
        for o in offers:
            all_product_ids.extend(o.product_ids)
        unique_product_ids = list(dict.fromkeys(all_product_ids))
        products_map = await cls._fetch_and_map_products(unique_product_ids)

        items = [cls._build_response(o, products_map) for o in offers]
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

        return items, total_count, total_pages

    # ─── PUBLIC STOREFRONT OPERATIONS ──────────────────────────────────────

    @classmethod
    async def get_active_public_offers(cls) -> List[SpecialOfferResponse]:
        """Fetch all currently active special offers for the customer-facing storefront.
        
        Strictly enforces: start_at <= now < end_at AND is_active is True.
        """
        curr_utc = now_utc()
        query = {
            "is_active": True,
            "start_at": {"$lte": curr_utc},
            "end_at": {"$gt": curr_utc},
        }

        active_offers = await SpecialOffer.find(query).sort("start_at").to_list()
        if not active_offers:
            return []

        # Batch populate products
        all_pids = []
        for o in active_offers:
            all_pids.extend(o.product_ids)
        unique_pids = list(dict.fromkeys(all_pids))
        products_map = await cls._fetch_and_map_products(unique_pids)

        # Filter to only published products if desired
        responses = []
        for o in active_offers:
            valid_products = [
                products_map[pid]
                for pid in o.product_ids
                if pid in products_map and products_map[pid].status != "archived"
            ]
            if valid_products:
                res = cls._build_response(o, products_map)
                res.products = valid_products
                responses.append(res)

        return responses
