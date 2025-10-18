"""
Tests for authentication module
"""

import pytest
import bcrypt
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from auth import AuthManager, auth_manager

class TestAuthManager:
    """Test cases for AuthManager class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.auth_manager = AuthManager()
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = self.auth_manager.hash_password(password)
        
        # Should be different from original
        assert hashed != password
        
        # Should be a string
        assert isinstance(hashed, str)
        
        # Should be verifiable
        assert self.auth_manager.verify_password(password, hashed)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = self.auth_manager.hash_password(password)
        
        assert self.auth_manager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = self.auth_manager.hash_password(password)
        
        assert self.auth_manager.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "test_password_123"
        invalid_hash = "invalid_hash"
        
        assert self.auth_manager.verify_password(password, invalid_hash) is False
    
    def test_create_session(self):
        """Test session creation."""
        username = "test_user"
        session_id = self.auth_manager.create_session(username)
        
        # Should be a string
        assert isinstance(session_id, str)
        
        # Should be in sessions
        assert session_id in self.auth_manager.user_sessions
        assert self.auth_manager.user_sessions[session_id] == username
    
    def test_get_current_user_valid_session(self):
        """Test getting current user with valid session."""
        username = "test_user"
        session_id = self.auth_manager.create_session(username)
        
        # Mock request object
        request = Mock()
        request.cookies = {"session_id": session_id}
        
        current_user = self.auth_manager.get_current_user(request)
        assert current_user == username
    
    def test_get_current_user_invalid_session(self):
        """Test getting current user with invalid session."""
        # Mock request object with invalid session
        request = Mock()
        request.cookies = {"session_id": "invalid_session"}
        
        current_user = self.auth_manager.get_current_user(request)
        assert current_user is None
    
    def test_get_current_user_no_session(self):
        """Test getting current user with no session."""
        # Mock request object with no session
        request = Mock()
        request.cookies = {}
        
        current_user = self.auth_manager.get_current_user(request)
        assert current_user is None
    
    def test_invalidate_session(self):
        """Test session invalidation."""
        username = "test_user"
        session_id = self.auth_manager.create_session(username)
        
        # Should be in sessions
        assert session_id in self.auth_manager.user_sessions
        
        # Invalidate session
        result = self.auth_manager.invalidate_session(session_id)
        assert result is True
        
        # Should not be in sessions
        assert session_id not in self.auth_manager.user_sessions
    
    def test_invalidate_nonexistent_session(self):
        """Test invalidating non-existent session."""
        result = self.auth_manager.invalidate_session("nonexistent_session")
        assert result is False
    
    def test_require_auth_valid_user(self):
        """Test require_auth with valid user."""
        username = "test_user"
        session_id = self.auth_manager.create_session(username)
        
        # Mock request object
        request = Mock()
        request.cookies = {"session_id": session_id}
        
        result = self.auth_manager.require_auth(request)
        assert result == username
    
    def test_require_auth_no_user(self):
        """Test require_auth with no user."""
        # Mock request object with no session
        request = Mock()
        request.cookies = {}
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_manager.require_auth(request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
    
    def test_require_admin_valid_admin(self):
        """Test require_admin with valid admin."""
        username = "admin"
        session_id = self.auth_manager.create_session(username)
        
        # Mock request object
        request = Mock()
        request.cookies = {"session_id": session_id}
        
        result = self.auth_manager.require_admin(request)
        assert result == username
    
    def test_require_admin_non_admin(self):
        """Test require_admin with non-admin user."""
        username = "regular_user"
        session_id = self.auth_manager.create_session(username)
        
        # Mock request object
        request = Mock()
        request.cookies = {"session_id": session_id}
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_manager.require_admin(request)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
