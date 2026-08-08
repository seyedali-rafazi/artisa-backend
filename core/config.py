"""Application configuration using Pydantic Settings."""

from typing import List, Optional
from urllib.parse import quote_plus

from decouple import config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Artisa API"
    VERSION: str = "1.0.0"
    DEBUG: bool = config("DEBUG", default=True, cast=bool)

    # Security
    SECRET_KEY: str = config("SECRET_KEY", default="artisa-secret-key-super-secure-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
        "JWT_ACCESS_TOKEN_LIFETIME", default=1440, cast=int
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = config(
        "JWT_REFRESH_TOKEN_LIFETIME", default=10080, cast=int
    )
    GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID", default="")
    GOOGLE_CLIENT_SECRET: str = config("GOOGLE_CLIENT_SECRET", default="")

    # Email (Resend)
    RESEND_API_KEY: str = config("RESEND_API_KEY", default="")
    FROM_EMAIL: str = config("FROM_EMAIL", default="Artisa <onboarding@resend.dev>")
    EMAIL_FROM: str = config("EMAIL_FROM", default=config("FROM_EMAIL", default="Artisa <onboarding@resend.dev>"))

    # MongoDB
    MONGODB_URI: str = config("MONGODB_URI", default="")
    MONGODB_USER: str = config("MONGODB_USER", default="")
    MONGODB_CLUSTER: str = config("MONGODB_CLUSTER", default="")
    MONGODB_NAME: str = config(
        "MONGODB_NAME", default=config("DATABASE_NAME", default="artisa_db")
    )
    MONGODB_PASSWORD: str = config("MONGODB_PASSWORD", default="")
    MONGODB_PASSWORD: str = config("MONGODB_PASSWORD", default="")

    # Vercel Blob (product images)
    BLOB_STORE_ID: str = config("BLOB_STORE_ID", default="")
    BLOB_READ_WRITE_TOKEN: str = config("BLOB_READ_WRITE_TOKEN", default="")

    # CORS
    CORS_ORIGINS: List[str] = config(
        "CORS_ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # Auth cookies
    #
    # COOKIE_SECURE  — must be True in production (cookies only sent over HTTPS).
    #                  Set to False only for local http://localhost development.
    # COOKIE_SAMESITE — "lax" works when the frontend and API share the same
    #                  site (or in local dev). Use "none" when the frontend is
    #                  hosted on a different domain than the API in production
    #                  (requires COOKIE_SECURE=True, per browser spec).
    # COOKIE_DOMAIN  — optional, e.g. ".bilitiko.com" to share the cookie across
    #                  subdomains. Leave unset for a host-only cookie.
    COOKIE_SECURE: bool = config("COOKIE_SECURE", default=True, cast=bool)
    COOKIE_SAMESITE: str = config("COOKIE_SAMESITE", default="none", cast=str)
    COOKIE_DOMAIN: str = config("COOKIE_DOMAIN", default="", cast=str)

    @property
    def cookie_domain(self) -> Optional[str]:
        """Return the cookie domain, or None for a host-only cookie."""
        return self.COOKIE_DOMAIN or None

    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection URL with password replacement if needed."""
        uri = self.MONGODB_URI

        if not uri:
            # Fall back to assembling a mongodb+srv:// URI from the split
            # MONGODB_USER / MONGODB_CLUSTER / MONGODB_PASSWORD settings.
            if not (self.MONGODB_USER and self.MONGODB_CLUSTER):
                raise RuntimeError(
                    "MongoDB is not configured. Set MONGODB_URI in your .env, "
                    "or set MONGODB_USER + MONGODB_CLUSTER (+ MONGODB_PASSWORD)."
                )
            encoded_password = (
                quote_plus(self.MONGODB_PASSWORD) if self.MONGODB_PASSWORD else ""
            )
            return (
                f"mongodb+srv://{self.MONGODB_USER}:{encoded_password}"
                f"@{self.MONGODB_CLUSTER}/{self.MONGODB_NAME}"
                f"?retryWrites=true&w=majority"
            )

        # If password placeholder exists and we have a password, replace it
        if "<db_password>" in uri and self.MONGODB_PASSWORD:
            # URL-encode the password for MongoDB connection
            encoded_password = quote_plus(self.MONGODB_PASSWORD)
            uri = uri.replace("<db_password>", encoded_password)

        return uri

    class Config:
        case_sensitive = True


settings = Settings()

# Made with Bob
