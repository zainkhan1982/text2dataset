"""
Tests for cache module
"""

import pytest
import asyncio
import time
from unittest.mock import patch
from cache import CacheManager, CacheDecorator, cached

class TestCacheManager:
    """Test cases for CacheManager class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cache = CacheManager(default_ttl=60)
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        key = "test_key"
        value = {"data": "test_value"}
        
        self.cache.set(key, value)
        retrieved = self.cache.get(key)
        
        assert retrieved == value
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        result = self.cache.get("nonexistent")
        assert result is None
    
    def test_get_with_default(self):
        """Test getting with default value."""
        default_value = "default"
        result = self.cache.get("nonexistent", default_value)
        assert result == default_value
    
    def test_delete(self):
        """Test key deletion."""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value)
        assert self.cache.get(key) == value
        
        result = self.cache.delete(key)
        assert result is True
        assert self.cache.get(key) is None
    
    def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        result = self.cache.delete("nonexistent")
        assert result is False
    
    def test_clear(self):
        """Test cache clearing."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        assert len(self.cache._cache) == 2
        
        self.cache.clear()
        assert len(self.cache._cache) == 0
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        key = "test_key"
        value = "test_value"
        
        # Set with very short TTL
        self.cache.set(key, value, ttl=1)
        assert self.cache.get(key) == value
        
        # Wait for expiration
        time.sleep(1.1)
        assert self.cache.get(key) is None
    
    def test_cleanup_expired(self):
        """Test expired entry cleanup."""
        # Set entries with different TTLs
        self.cache.set("short", "value1", ttl=1)
        self.cache.set("long", "value2", ttl=60)
        
        # Wait for short entry to expire
        time.sleep(1.1)
        
        # Cleanup should remove expired entries
        removed_count = self.cache.cleanup_expired()
        assert removed_count == 1
        
        # Long entry should still be there
        assert self.cache.get("long") == "value2"
        # Short entry should be gone
        assert self.cache.get("short") is None
    
    def test_get_stats(self):
        """Test cache statistics."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        # Access one key multiple times
        self.cache.get("key1")
        self.cache.get("key1")
        
        stats = self.cache.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["total_access_count"] >= 2
    
    def test_complex_data_types(self):
        """Test caching complex data types."""
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": {"value": 42}},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3}
        }
        
        self.cache.set("complex", complex_data)
        retrieved = self.cache.get("complex")
        
        assert retrieved == complex_data
    
    def test_thread_safety(self):
        """Test thread safety with concurrent access."""
        import threading
        
        def set_values():
            for i in range(100):
                self.cache.set(f"key_{i}", f"value_{i}")
        
        def get_values():
            for i in range(100):
                self.cache.get(f"key_{i}")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=set_values))
            threads.append(threading.Thread(target=get_values))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache integrity
        stats = self.cache.get_stats()
        assert stats["total_entries"] == 100

class TestCacheDecorator:
    """Test cases for CacheDecorator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cache = CacheManager(default_ttl=60)
        self.decorator = CacheDecorator(self.cache, ttl=30)
    
    def test_sync_function_caching(self):
        """Test caching of synchronous functions."""
        call_count = 0
        
        @self.decorator
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(2, 3)
        assert result1 == 5
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(2, 3)
        assert result2 == 5
        assert call_count == 1  # Should not have increased
    
    def test_async_function_caching(self):
        """Test caching of asynchronous functions."""
        call_count = 0
        
        @self.decorator
        async def expensive_async_function(x, y):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate async work
            return x * y
        
        async def test_async_caching():
            # First call should execute function
            result1 = await expensive_async_function(3, 4)
            assert result1 == 12
            assert call_count == 1
            
            # Second call should use cache
            result2 = await expensive_async_function(3, 4)
            assert result2 == 12
            assert call_count == 1  # Should not have increased
        
        asyncio.run(test_async_caching())
    
    def test_different_arguments(self):
        """Test that different arguments produce different cache keys."""
        call_count = 0
        
        @self.decorator
        def func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # Different arguments should not use cache
        result1 = func(1, 2)
        result2 = func(2, 3)
        
        assert result1 == 3
        assert result2 == 5
        assert call_count == 2  # Both calls should execute
    
    def test_keyword_arguments(self):
        """Test caching with keyword arguments."""
        call_count = 0
        
        @self.decorator
        def func(x, y=0):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # Same arguments with different order should use cache
        result1 = func(1, y=2)
        result2 = func(x=1, y=2)
        
        assert result1 == 3
        assert result2 == 3
        assert call_count == 1  # Only first call should execute

class TestCachedDecorator:
    """Test cases for the cached decorator."""
    
    def test_cached_decorator(self):
        """Test the cached decorator function."""
        call_count = 0
        
        @cached(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1
