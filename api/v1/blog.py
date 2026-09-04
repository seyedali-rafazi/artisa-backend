"""Blog Router — Public & Admin Endpoints."""

from datetime import datetime
import re
import uuid
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies.permissions import require_admin
from models.blog import Article
from models.user import User
from schemas.blog import (
    ArticleCreateRequest,
    ArticleResponse,
    ArticleUpdateRequest,
    PaginatedArticlesResponse,
)
from schemas.response import error_response, success_response
from services.audit_service import AuditLogService
from services.blob_storage import delete_file
from services.image_upload import cleanup_replaced_urls

router = APIRouter()
admin_blog_router = APIRouter(prefix="/admin/blog", tags=["Admin Blog"])


def serialize_article(a: Article) -> ArticleResponse:
    """Map Article Beanie document to ArticleResponse schema."""
    return ArticleResponse(
        id=a.articleId or str(a.id),
        articleId=a.articleId,
        title=a.title,
        desc=a.desc or "",
        content=a.content or "",
        date=a.date or "",
        author=a.author or "تیم تحریریه آرتیسا",
        image=a.image or "",
        created_at=a.created_at,
        updated_at=getattr(a, "updated_at", a.created_at),
    )


def extract_plain_text(html_or_text: Optional[str], max_len: int = 200) -> str:
    """Extract plain text summary from rich HTML content."""
    if not html_or_text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", html_or_text)
    clean = " ".join(clean.split())
    if len(clean) > max_len:
        return clean[:max_len] + "..."
    return clean


# ─── PUBLIC ENDPOINTS ─────────────────────────────────────────────────────────


@router.get("/articles", summary="Get blog articles list")
async def list_articles(
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = Query(None),
):
    """Retrieve all blog articles, optionally paginated with search."""
    query_filter = {}
    if search and search.strip():
        query_filter = {
            "$or": [
                {"title": {"$regex": search.strip(), "$options": "i"}},
                {"desc": {"$regex": search.strip(), "$options": "i"}},
                {"author": {"$regex": search.strip(), "$options": "i"}},
            ]
        }

    query = Article.find(query_filter).sort("-created_at")

    # If pagination params are provided, return paginated envelope
    if page is not None and limit is not None:
        total = await query.count()
        skip = (page - 1) * limit
        articles = await query.skip(skip).limit(limit).to_list()
        items = [serialize_article(a) for a in articles]
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return success_response(
            data=PaginatedArticlesResponse(
                items=items,
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages,
            ).model_dump(),
            message="لیست مقالات بلاگ دریافت شد",
        )

    # Otherwise return flat list for direct API compatibility
    articles = await query.to_list()
    items = [serialize_article(a).model_dump() for a in articles]
    return success_response(data=items, message="لیست مقالات بلاگ دریافت شد")


@router.get("/articles/{id}", summary="Get single blog article")
async def get_article(id: str):
    """Retrieve single blog article by articleId or mongo ID."""
    article = await Article.find_one(Article.articleId == id)
    if not article:
        try:
            article = await Article.get(PydanticObjectId(id))
        except Exception:
            pass

    if not article:
        return error_response(
            message="مقاله مورد نظر یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    data = serialize_article(article).model_dump()
    return success_response(data=data, message="اطلاعات مقاله دریافت شد")


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────


@admin_blog_router.get("/articles", summary="List articles for admin management")
async def admin_list_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin),
):
    """Retrieve paginated blog articles for admin panel."""
    query_filter = {}
    if search and search.strip():
        query_filter = {
            "$or": [
                {"title": {"$regex": search.strip(), "$options": "i"}},
                {"desc": {"$regex": search.strip(), "$options": "i"}},
                {"author": {"$regex": search.strip(), "$options": "i"}},
            ]
        }

    query = Article.find(query_filter).sort("-created_at")
    total = await query.count()
    skip = (page - 1) * limit
    articles = await query.skip(skip).limit(limit).to_list()

    items = [serialize_article(a) for a in articles]
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return success_response(
        data=PaginatedArticlesResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ).model_dump(),
        message="لیست مقالات مدیریت دریافت شد",
    )


@admin_blog_router.post(
    "/articles", status_code=status.HTTP_201_CREATED, summary="Create blog article"
)
async def admin_create_article(
    payload: ArticleCreateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Create a new blog article with rich content and cover image."""
    unique_id = f"art-{uuid.uuid4().hex[:8]}"

    desc = payload.desc
    if not desc or not desc.strip():
        desc = extract_plain_text(payload.content)

    author = payload.author or admin_user.name or "تیم تحریریه آرتیسا"
    date_val = payload.date or datetime.now().strftime("%Y/%m/%d")

    article = Article(
        articleId=unique_id,
        title=payload.title.strip(),
        desc=desc,
        content=payload.content or "",
        date=date_val,
        author=author,
        image=payload.image.strip(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await article.insert()

    await AuditLogService.log_action(
        user=admin_user,
        action="CREATE_BLOG_ARTICLE",
        resource=f"article_{article.articleId}",
        details={"title": article.title, "author": article.author},
        request=request,
    )

    return success_response(
        data=serialize_article(article).model_dump(),
        message="مقاله جدید با موفقیت ایجاد شد",
        status_code=status.HTTP_201_CREATED,
    )


@admin_blog_router.put("/articles/{id}", summary="Update blog article")
async def admin_update_article(
    id: str,
    payload: ArticleUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update an existing blog article and clean up replaced cover images."""
    article = await Article.find_one(Article.articleId == id)
    if not article:
        try:
            article = await Article.get(PydanticObjectId(id))
        except Exception:
            pass

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="مقاله یافت نشد"
        )

    previous_image = article.image
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        if val is not None:
            setattr(article, field, val)

    # Auto-update desc if content was updated and desc was empty
    if "content" in update_data and (not article.desc or not article.desc.strip()):
        article.desc = extract_plain_text(article.content)

    article.updated_at = datetime.utcnow()
    await article.save()

    # Clean up old image if changed
    if payload.image and payload.image != previous_image:
        await cleanup_replaced_urls(
            previous_urls=[previous_image], next_urls=[payload.image]
        )

    await AuditLogService.log_action(
        user=admin_user,
        action="UPDATE_BLOG_ARTICLE",
        resource=f"article_{article.articleId}",
        details={"title": article.title},
        request=request,
    )

    return success_response(
        data=serialize_article(article).model_dump(),
        message="مقاله با موفقیت بروزرسانی شد",
    )


@admin_blog_router.delete("/articles/{id}", summary="Delete blog article")
async def admin_delete_article(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Permanently delete a blog article and its cover image."""
    article = await Article.find_one(Article.articleId == id)
    if not article:
        try:
            article = await Article.get(PydanticObjectId(id))
        except Exception:
            pass

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="مقاله یافت نشد"
        )

    image_url = article.image
    title = article.title
    article_id = article.articleId

    await article.delete()

    if image_url:
        try:
            await delete_file([image_url])
        except Exception:
            pass

    await AuditLogService.log_action(
        user=admin_user,
        action="DELETE_BLOG_ARTICLE",
        resource=f"article_{article_id}",
        details={"title": title},
        request=request,
    )

    return success_response(
        data={"id": article_id},
        message="مقاله با موفقیت حذف شد",
    )
