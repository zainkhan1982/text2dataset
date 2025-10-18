"""
Caching utilities for improved performance
"""

import asyncio
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced caching manager with TTL and serialization."""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._cleanup_task = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = f"{prefix}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if 'expires_at' not in entry:
            return True
        return datetime.now() > entry['expires_at']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with TTL."""
        ttl = ttl or self._default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        try:
            # Serialize the value
            serialized_value = pickle.dumps(value)
            self._cache[key] = {
                'value': serialized_value,
                'expires_at': expires_at,
                'created_at': datetime.now(),
                'access_count': 0
            }
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Error caching value for key {key}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        if key not in self._cache:
            return default
        
        entry = self._cache[key]
        
        # Check if expired
        if self._is_expired(entry):
            del self._cache[key]
            logger.debug(f"Cache expired: {key}")
            return default
        
        # Update access count and timestamp
        entry['access_count'] += 1
        entry['last_accessed'] = datetime.now()
        
        try:
            # Deserialize the value
            value = pickle.loads(entry['value'])
            logger.debug(f"Cache hit: {key}")
            return value
        except Exception as e:
            logger.error(f"Error retrieving cached value for key {key}: {e}")
            del self._cache[key]
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if self._is_expired(entry))
        
        total_access_count = sum(entry.get('access_count', 0) for entry in self._cache.values())
        avg_access_count = total_access_count / total_entries if total_entries > 0 else 0
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'total_access_count': total_access_count,
            'average_access_count': avg_access_count,
            'memory_usage_estimate': sum(len(str(entry)) for entry in self._cache.values())
        }
    
    async def start_cleanup_task(self, interval: int = 300):
        """Start background cleanup task."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval)
                self.cleanup_expired()
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started cache cleanup task (interval: {interval}s)")

class CacheDecorator:
    """Decorator for caching function results."""
    
    def __init__(self, cache_manager: CacheManager, ttl: int = 300, key_prefix: str = ""):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.key_prefix = key_prefix
    
    def __call__(self, func):
        async def async_wrapper(*args, **kwargs):
            cache_key = self.cache_manager._generate_key(
                f"{self.key_prefix}{func.__name__}", 
                *args, 
                **kwargs
            )
            
            # Try to get from cache
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self.cache_manager.set(cache_key, result, self.ttl)
            return result
        
        def sync_wrapper(*args, **kwargs):
            cache_key = self.cache_manager._generate_key(
                f"{self.key_prefix}{func.__name__}", 
                *args, 
                **kwargs
            )
            
            # Try to get from cache
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            self.cache_manager.set(cache_key, result, self.ttl)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

# Global cache manager instance
cache_manager = CacheManager(default_ttl=300)

# Decorator for easy caching
def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    return CacheDecorator(cache_manager, ttl, key_prefix)
