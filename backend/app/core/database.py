"""
MongoDB database connection and management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_db():
    """Initialize MongoDB connection."""
    global _client, _db
    try:
        _client = AsyncIOMotorClient(settings.mongo_uri)
        _db = _client[settings.mongo_db_name]
        # Verify connection
        await _client.admin.command("ping")
        logger.info(f"✅ Connected to MongoDB: {settings.mongo_db_name}")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def close_db():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_db():
    """Get database instance."""
    return _db


def get_collection(name: str):
    """Get a specific collection."""
    return _db[name]
