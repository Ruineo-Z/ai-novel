import redis
from app.core.config import settings
from typing import Optional
import json

class RedisClient:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        return self.redis_client.get(key)
    
    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """设置缓存值"""
        return self.redis_client.setex(key, expire, value)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """获取JSON格式的缓存值"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(self, key: str, value: dict, expire: int = 3600) -> bool:
        """设置JSON格式的缓存值"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, expire)
        except (TypeError, ValueError):
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return bool(self.redis_client.delete(key))
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return bool(self.redis_client.exists(key))

redis_client = RedisClient()