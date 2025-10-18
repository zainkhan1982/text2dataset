"""
Utility functions and helpers
"""

import os
import re
import hashlib
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    """File validation utilities."""
    
    @staticmethod
    def validate_file_upload(file: UploadFile, max_size: int = 10 * 1024 * 1024) -> bool:
        """Validate uploaded file for security and type."""
        if not file.filename:
            return False
        
        # Check file extension
        allowed_extensions = {'.txt', '.pdf', '.docx', '.doc'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            logger.warning(f"Invalid file extension: {file_ext}")
            return False
        
        # Check file size
        if hasattr(file, 'size') and file.size > max_size:
            logger.warning(f"File too large: {file.size} bytes")
            return False
        
        # Check for suspicious filenames
        suspicious_patterns = ['..', '/', '\\', '<', '>', ':', '|', '*', '?']
        if any(pattern in file.filename for pattern in suspicious_patterns):
            logger.warning(f"Suspicious filename: {file.filename}")
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading dots and spaces
        filename = filename.lstrip('. ')
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        return filename

class TextProcessor:
    """Text processing utilities."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespaces
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_text_length(text: str, min_length: int = 10, max_length: int = 1000000) -> bool:
        """Validate text length."""
        if not text or len(text.strip()) < min_length:
            return False
        if len(text) > max_length:
            return False
        return True

class SecurityUtils:
    """Security-related utilities."""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_content(content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent XSS."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove script tags and their content
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove javascript: and data: protocols
        text = re.sub(r'(javascript|data):', '', text, flags=re.IGNORECASE)
        return text.strip()

class ResponseBuilder:
    """Utility class for building API responses."""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Build a success response."""
        response = {"success": True, "message": message}
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error_response(message: str, status_code: int = 400, details: Any = None) -> Dict[str, Any]:
        """Build an error response."""
        response = {"success": False, "error": message}
        if details is not None:
            response["details"] = details
        return response
    
    @staticmethod
    def paginated_response(data: List[Any], page: int, per_page: int, total: int) -> Dict[str, Any]:
        """Build a paginated response."""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }

class CacheManager:
    """Simple in-memory cache manager."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if key in self._cache:
            return self._cache[key]
        return default
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        import time
        self._cache[key] = value
        self._timestamps[key] = time.time() + ttl
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            return True
        return False
    
    def cleanup_expired(self) -> None:
        """Clean up expired cache entries."""
        import time
        current_time = time.time()
        expired_keys = [key for key, timestamp in self._timestamps.items() if timestamp < current_time]
        for key in expired_keys:
            self.delete(key)

# Global instances
file_validator = FileValidator()
text_processor = TextProcessor()
security_utils = SecurityUtils()
response_builder = ResponseBuilder()
cache_manager = CacheManager()
