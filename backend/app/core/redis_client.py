"""
成长印记 - Redis 客户端模块
"""
import redis.asyncio as redis
from typing import Optional

from app.core.config import settings

# Redis 客户端实例
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def set_cache(key: str, value: str, expire: int = 3600):
    """设置缓存"""
    r = await get_redis()
    await r.setex(key, expire, value)


async def get_cache(key: str) -> Optional[str]:
    """获取缓存"""
    r = await get_redis()
    return await r.get(key)


async def delete_cache(key: str):
    """删除缓存"""
    r = await get_redis()
    await r.delete(key)


async def set_sms_code(phone: str, code: str, expire: int = 300):
    """设置短信验证码"""
    await set_cache(f"sms:{phone}", code, expire)


async def get_sms_code(phone: str) -> Optional[str]:
    """获取短信验证码"""
    return await get_cache(f"sms:{phone}")


async def delete_sms_code(phone: str):
    """删除短信验证码"""
    await delete_cache(f"sms:{phone}")
