"""Database configuration and initialization."""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.config import settings

from models.user import User
from models.product import Product
from models.comment import Comment
from models.address import Address
from models.order import Order
from models.wishlist import Wishlist
from models.blog import Article
from models.faq import FAQ
from models.banner import Banner


class Database:
    """Database connection manager."""

    client: AsyncIOMotorClient = None

    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB and initialize Beanie."""
        cls.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            directConnection=False,
            retryWrites=True,
            w="majority",
        )

        # Initialize Beanie with all document models
        await init_beanie(
            database=cls.client[settings.MONGODB_NAME],
            document_models=[
                User,
                Product,
                Comment,
                Address,
                Order,
                Wishlist,
                Article,
                FAQ,
                Banner,
            ],
        )
        print(f"Connected to MongoDB: {settings.MONGODB_NAME}")

    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            print("Closed MongoDB connection")


# Database instance
db = Database()
