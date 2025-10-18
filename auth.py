"""
Authentication and authorization utilities
"""

import bcrypt
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Handles authentication and session management."""
    
    def __init__(self):
        self.user_sessions: Dict[str, str] = {}  # session_id -> username
        self.session_timeout = 3600  # 1 hour
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt for secure storage."""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a bcrypt hashed password."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def create_session(self, username: str) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        self.user_sessions[session_id] = username
        logger.info(f"Created session for user: {username}")
        return session_id
    
    def get_current_user(self, request: Request) -> Optional[str]:
        """Get the current user from the session cookie."""
        session_id = request.cookies.get("session_id")
        if session_id and session_id in self.user_sessions:
            return self.user_sessions[session_id]
        return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a user session."""
        if session_id in self.user_sessions:
            username = self.user_sessions[session_id]
            del self.user_sessions[session_id]
            logger.info(f"Invalidated session for user: {username}")
            return True
        return False
    
    def require_auth(self, request: Request) -> str:
        """Require authentication and return username."""
        user = self.get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user
    
    def require_admin(self, request: Request) -> str:
        """Require admin authentication."""
        user = self.require_auth(request)
        if user != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (placeholder for future implementation)."""
        # In a production system, you'd implement session expiration logic here
        pass

# Global auth manager instance
auth_manager = AuthManager()
