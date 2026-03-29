import redis.asyncio as redis
from app.core.config import settings
import json
from typing import Optional, Any

# Global Redis client
redis_client: Optional[redis.Redis] = None

async def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        print("Redis connection established.")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        print("Redis connection closed.")

def get_redis_client() -> Optional[redis.Redis]:
    return redis_client

# Caching Utilities
async def get_cached_data(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Cache get error: {e}")
    return None

async def set_cached_data(key: str, data: Any, ttl: int = 3600):
    if not redis_client:
        return
    try:
        await redis_client.setex(key, ttl, json.dumps(data))
    except Exception as e:
        print(f"Cache set error: {e}")
