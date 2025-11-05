from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from gridfs import GridFS
from pymongo import MongoClient
from app.config import settings


_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def get_db() -> AsyncIOMotorDatabase:
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
        _db = _client[settings.mongodb_db]
    return _db


def get_sync_gridfs() -> GridFS:
    # GridFS requires sync client; use for streaming store with encryption wrapper
    sync_client = MongoClient(settings.mongodb_uri)
    sync_db = sync_client[settings.mongodb_db]
    return GridFS(sync_db)

