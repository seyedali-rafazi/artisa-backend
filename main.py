"""Main FastAPI application for Artisa."""

from contextlib import asynccontextmanager

from beanie import PydanticObjectId
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import db

# Import API V1 Routers
from api.v1 import (
    auth_router,
    users_router,
    products_router,
    comments_router,
    addresses_router,
    orders_router,
    wishlist_router,
    favorites_router,
    blog_router,
    faqs_router,
    banners_router,
    uploads_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Connect to MongoDB & initialize Beanie
    await db.connect_db()
    yield
    # Close database connection
    await db.close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Artisa Online Gallery & E-Commerce RESTful API",
    lifespan=lifespan,
    json_encoders={
        PydanticObjectId: str,
        ObjectId: str,
    },
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product images are stored in Vercel Blob (public URLs), not on the
# ephemeral Vercel filesystem. Legacy /uploads URLs may still exist in MongoDB
# until migrated; they are no longer served by this application.


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail if isinstance(exc.detail, str) else "Error occurred",
            "errors": [exc.detail] if not isinstance(exc.detail, str) else [],
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", [])])
        msg = err.get("msg", "")
        formatted_errors.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "خطای اعتبار سنجی ورودی‌ها",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "خطای داخلی سرور",
            "errors": [str(exc)] if settings.DEBUG else [],
        },
    )


# Include API V1 Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(comments_router, prefix="/api/v1", tags=["Comments"])
app.include_router(addresses_router, prefix="/api/v1/addresses", tags=["Addresses"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(wishlist_router, prefix="/api/v1/wishlist", tags=["Wishlist"])
app.include_router(favorites_router, prefix="/api/v1/favorites", tags=["Favorites"])
app.include_router(blog_router, prefix="/api/v1/blog", tags=["Blog"])
app.include_router(faqs_router, prefix="/api/v1/faqs", tags=["FAQs"])
app.include_router(banners_router, prefix="/api/v1/banners", tags=["Banners"])
app.include_router(uploads_router, prefix="/api/v1/upload", tags=["Uploads"])
app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])


@app.get("/", tags=["Root"])
async def root():
    """Root status endpoint."""
    return {
        "success": True,
        "message": f"Welcome to {settings.APP_NAME} v{settings.VERSION}",
        "data": {"docs": "/docs", "openapi": "/openapi.json"},
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
