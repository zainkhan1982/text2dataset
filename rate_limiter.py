"""
Rate limiting utilities for API endpoints
"""

import time
from typing import Dict, Optional
from collections import defaultdict, deque
import asyncio
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: Optional[int] = None):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.tokens = self.burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def is_allowed(self) -> bool:
        """Check if request is allowed based on rate limit."""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            
            # Add tokens based on time passed
            tokens_to_add = time_passed * (self.requests_per_minute / 60)
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            return False
    
    def get_reset_time(self) -> float:
        """Get time when rate limit will reset."""
        if self.tokens >= 1:
            return 0
        
        tokens_needed = 1 - self.tokens
        return tokens_needed / (self.requests_per_minute / 60)

class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, requests_per_minute: int = 60, window_size: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size  # in seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for the given identifier."""
        async with self._lock:
            now = time.time()
            window_start = now - self.window_size
            
            # Clean old requests
            request_times = self.requests[identifier]
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Check if under limit
            if len(request_times) < self.requests_per_minute:
                request_times.append(now)
                return True
            
            return False
    
    def get_reset_time(self, identifier: str) -> float:
        """Get time when rate limit will reset for the identifier."""
        request_times = self.requests.get(identifier, deque())
        if not request_times:
            return 0
        
        if len(request_times) < self.requests_per_minute:
            return 0
        
        oldest_request = request_times[0]
        return oldest_request + self.window_size - time.time()

class GlobalRateLimiter:
    """Global rate limiter manager."""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.user_limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self._lock = asyncio.Lock()
    
    async def get_limiter(self, endpoint: str, requests_per_minute: int = 60) -> RateLimiter:
        """Get or create a rate limiter for an endpoint."""
        async with self._lock:
            if endpoint not in self.limiters:
                self.limiters[endpoint] = RateLimiter(requests_per_minute)
            return self.limiters[endpoint]
    
    async def get_user_limiter(self, user_id: str, requests_per_minute: int = 100) -> SlidingWindowRateLimiter:
        """Get or create a rate limiter for a user."""
        async with self._lock:
            if user_id not in self.user_limiters:
                self.user_limiters[user_id] = SlidingWindowRateLimiter(requests_per_minute)
            return self.user_limiters[user_id]
    
    async def check_rate_limit(self, endpoint: str, user_id: Optional[str] = None, 
                             requests_per_minute: int = 60) -> tuple[bool, float]:
        """Check rate limit for endpoint and optionally user."""
        # Check endpoint rate limit
        endpoint_limiter = await self.get_limiter(endpoint, requests_per_minute)
        if not await endpoint_limiter.is_allowed():
            reset_time = endpoint_limiter.get_reset_time()
            logger.warning(f"Endpoint rate limit exceeded for {endpoint}")
            return False, reset_time
        
        # Check user rate limit if user_id provided
        if user_id:
            user_limiter = await self.get_user_limiter(user_id, requests_per_minute * 2)
            if not await user_limiter.is_allowed(user_id):
                reset_time = user_limiter.get_reset_time(user_id)
                logger.warning(f"User rate limit exceeded for {user_id}")
                return False, reset_time
        
        return True, 0

# Global rate limiter instance
rate_limiter = GlobalRateLimiter()

def rate_limit(requests_per_minute: int = 60):
    """Decorator for rate limiting endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and user info from FastAPI context
            request = None
            user_id = None
            
            for arg in args:
                if hasattr(arg, 'cookies'):  # FastAPI Request object
                    request = arg
                    # Try to get user from session
                    session_id = request.cookies.get("session_id")
                    if session_id:
                        # This would need to be integrated with your auth system
                        user_id = session_id
                    break
            
            endpoint = func.__name__
            allowed, reset_time = await rate_limiter.check_rate_limit(
                endpoint, user_id, requests_per_minute
            )
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {reset_time:.1f} seconds."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
