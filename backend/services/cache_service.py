from redis import Redis
import json
import os
from typing import Optional, Any

class CacheService:
    """Service for Redis cache operations (Single Responsibility)"""
    
    def __init__(self):
        self.redis = Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or self.default_ttl
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return self.redis.exists(key) > 0
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in cache"""
        return self.redis.incr(key, amount)
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key"""
        return self.redis.expire(key, ttl)

cache_service = CacheService()