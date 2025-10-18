"""
Tests for utility modules
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi import UploadFile
from utils import FileValidator, TextProcessor, SecurityUtils, ResponseBuilder

class TestFileValidator:
    """Test cases for FileValidator class."""
    
    def test_validate_file_upload_valid_txt(self):
        """Test file validation with valid txt file."""
        # Mock UploadFile
        file = Mock(spec=UploadFile)
        file.filename = "test.txt"
        file.size = 1024  # 1KB
        
        result = FileValidator.validate_file_upload(file)
        assert result is True
    
    def test_validate_file_upload_valid_pdf(self):
        """Test file validation with valid PDF file."""
        # Mock UploadFile
        file = Mock(spec=UploadFile)
        file.filename = "document.pdf"
        file.size = 1024  # 1KB
        
        result = FileValidator.validate_file_upload(file)
        assert result is True
    
    def test_validate_file_upload_invalid_extension(self):
        """Test file validation with invalid extension."""
        # Mock UploadFile
        file = Mock(spec=UploadFile)
        file.filename = "script.exe"
        file.size = 1024
        
        result = FileValidator.validate_file_upload(file)
        assert result is False
    
    def test_validate_file_upload_no_filename(self):
        """Test file validation with no filename."""
        # Mock UploadFile
        file = Mock(spec=UploadFile)
        file.filename = None
        file.size = 1024
        
        result = FileValidator.validate_file_upload(file)
        assert result is False
    
    def test_validate_file_upload_too_large(self):
        """Test file validation with file too large."""
        # Mock UploadFile
        file = Mock(spec=UploadFile)
        file.filename = "large.txt"
        file.size = 20 * 1024 * 1024  # 20MB
        
        result = FileValidator.validate_file_upload(file, max_size=10 * 1024 * 1024)
        assert result is False
    
    def test_validate_file_upload_suspicious_filename(self):
        """Test file validation with suspicious filename."""
        # Mock UploadFile
        file = Mock(spec=UploadFile)
        file.filename = "../../../etc/passwd"
        file.size = 1024
        
        result = FileValidator.validate_file_upload(file)
        assert result is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test dangerous characters
        filename = "test<>:\"/\\|?*.txt"
        sanitized = FileValidator.sanitize_filename(filename)
        assert sanitized == "test_________.txt"
        
        # Test leading dots
        filename = "...test.txt"
        sanitized = FileValidator.sanitize_filename(filename)
        assert sanitized == "test.txt"
        
        # Test long filename
        filename = "a" * 300 + ".txt"
        sanitized = FileValidator.sanitize_filename(filename)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")

class TestTextProcessor:
    """Test cases for TextProcessor class."""
    
    def test_clean_text_normal(self):
        """Test text cleaning with normal text."""
        text = "  Hello   world  \n\n  "
        cleaned = TextProcessor.clean_text(text)
        assert cleaned == "Hello world"
    
    def test_clean_text_empty(self):
        """Test text cleaning with empty text."""
        text = ""
        cleaned = TextProcessor.clean_text(text)
        assert cleaned == ""
    
    def test_clean_text_none(self):
        """Test text cleaning with None."""
        text = None
        cleaned = TextProcessor.clean_text(text)
        assert cleaned == ""
    
    def test_validate_text_length_valid(self):
        """Test text length validation with valid text."""
        text = "This is a valid text with sufficient length."
        result = TextProcessor.validate_text_length(text)
        assert result is True
    
    def test_validate_text_length_too_short(self):
        """Test text length validation with too short text."""
        text = "Short"
        result = TextProcessor.validate_text_length(text, min_length=10)
        assert result is False
    
    def test_validate_text_length_too_long(self):
        """Test text length validation with too long text."""
        text = "a" * 1000001  # Over 1MB
        result = TextProcessor.validate_text_length(text, max_length=1000000)
        assert result is False

class TestSecurityUtils:
    """Test cases for SecurityUtils class."""
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        token = SecurityUtils.generate_secure_token()
        
        # Should be a string
        assert isinstance(token, str)
        
        # Should have reasonable length
        assert len(token) >= 32
        
        # Should be URL-safe
        assert all(c.isalnum() or c in '-_' for c in token)
    
    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length."""
        token = SecurityUtils.generate_secure_token(16)
        assert len(token) >= 16
    
    def test_hash_content(self):
        """Test content hashing."""
        content = "test content"
        hash1 = SecurityUtils.hash_content(content)
        hash2 = SecurityUtils.hash_content(content)
        
        # Should be consistent
        assert hash1 == hash2
        
        # Should be different for different content
        hash3 = SecurityUtils.hash_content("different content")
        assert hash1 != hash3
        
        # Should be a string
        assert isinstance(hash1, str)
    
    def test_sanitize_input_normal(self):
        """Test input sanitization with normal text."""
        text = "Hello world"
        sanitized = SecurityUtils.sanitize_input(text)
        assert sanitized == "Hello world"
    
    def test_sanitize_input_html_tags(self):
        """Test input sanitization with HTML tags."""
        text = "<script>alert('xss')</script>Hello"
        sanitized = SecurityUtils.sanitize_input(text)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
    
    def test_sanitize_input_javascript_protocol(self):
        """Test input sanitization with javascript protocol."""
        text = "javascript:alert('xss')"
        sanitized = SecurityUtils.sanitize_input(text)
        assert "javascript:" not in sanitized
    
    def test_sanitize_input_data_protocol(self):
        """Test input sanitization with data protocol."""
        text = "data:text/html,<script>alert('xss')</script>"
        sanitized = SecurityUtils.sanitize_input(text)
        assert "data:" not in sanitized

class TestResponseBuilder:
    """Test cases for ResponseBuilder class."""
    
    def test_success_response_no_data(self):
        """Test success response without data."""
        response = ResponseBuilder.success_response()
        
        assert response["success"] is True
        assert response["message"] == "Success"
        assert "data" not in response
    
    def test_success_response_with_data(self):
        """Test success response with data."""
        data = {"key": "value"}
        response = ResponseBuilder.success_response(data, "Custom message")
        
        assert response["success"] is True
        assert response["message"] == "Custom message"
        assert response["data"] == data
    
    def test_error_response_basic(self):
        """Test basic error response."""
        response = ResponseBuilder.error_response("Test error")
        
        assert response["success"] is False
        assert response["error"] == "Test error"
        assert "details" not in response
    
    def test_error_response_with_details(self):
        """Test error response with details."""
        details = {"field": "validation_error"}
        response = ResponseBuilder.error_response("Validation failed", details=details)
        
        assert response["success"] is False
        assert response["error"] == "Validation failed"
        assert response["details"] == details
    
    def test_paginated_response(self):
        """Test paginated response."""
        data = [{"id": 1}, {"id": 2}]
        response = ResponseBuilder.paginated_response(data, page=1, per_page=10, total=25)
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["pagination"]["page"] == 1
        assert response["pagination"]["per_page"] == 10
        assert response["pagination"]["total"] == 25
        assert response["pagination"]["pages"] == 3  # ceil(25/10)
