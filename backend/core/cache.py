import redis.asyncio as aioredis
import json
from typing import Optional, Any
from core.config import get_settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is None:
        try:
            s = get_settings()
            _redis = aioredis.from_url(s.redis_url, decode_responses=True, socket_connect_timeout=2)
            await _redis.ping()
        except Exception:
            _redis = None  # demo mode: no cache
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    if not r:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = None) -> bool:
    r = await get_redis()
    if not r:
        return False
    try:
        s = get_settings()
        await r.setex(key, ttl or s.cache_ttl_seconds, json.dumps(value))
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    r = await get_redis()
    if not r:
        return False
    try:
        await r.delete(key)
        return True
    except Exception:
        return False
