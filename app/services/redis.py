import redis.asyncio as redis

from app.settings import settings

redis_client = redis.from_url(
    settings.REDIS_URL.unicode_string(), encoding="utf-8", decode_responses=True
)
