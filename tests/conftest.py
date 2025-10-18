"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the main app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from auth import auth_manager
from cache import cache_manager

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def mock_request():
    """Create a mock FastAPI request object."""
    request = Mock()
    request.cookies = {}
    request.headers = {}
    request.method = "GET"
    request.url = "http://test.com"
    return request

@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile object."""
    file = Mock()
    file.filename = "test.txt"
    file.content_type = "text/plain"
    file.size = 1024
    file.read = Mock(return_value=b"test content")
    return file

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Apple Inc. is an American multinational technology company headquartered in Cupertino, California.
    It was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976.
    Apple is the world's largest technology company by revenue, with US$394.3 billion in 2022 revenue.
    The company's products include the iPhone smartphone, iPad tablet computer, Mac personal computers,
    iPod portable media player, Apple Watch smartwatch, Apple TV digital media player, and AirPods wireless earbuds.
    """

@pytest.fixture
def sample_dataset():
    """Sample dataset for testing."""
    return [
        {"text": "Apple Inc. is a technology company.", "entity": "Apple Inc.", "label": "ORG"},
        {"text": "It was founded in April 1976.", "entity": "April 1976", "label": "DATE"},
        {"text": "The company is headquartered in Cupertino.", "entity": "Cupertino", "label": "GPE"}
    ]

@pytest.fixture
def authenticated_user():
    """Create an authenticated user for testing."""
    username = "test_user"
    session_id = auth_manager.create_session(username)
    
    mock_request = Mock()
    mock_request.cookies = {"session_id": session_id}
    
    return {
        "username": username,
        "session_id": session_id,
        "request": mock_request
    }

@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    username = "admin"
    session_id = auth_manager.create_session(username)
    
    mock_request = Mock()
    mock_request.cookies = {"session_id": session_id}
    
    return {
        "username": username,
        "session_id": session_id,
        "request": mock_request
    }

@pytest.fixture(autouse=True)
def cleanup_cache():
    """Clean up cache after each test."""
    yield
    cache_manager.clear()

@pytest.fixture(autouse=True)
def cleanup_auth():
    """Clean up auth sessions after each test."""
    yield
    auth_manager.user_sessions.clear()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add unit marker to all tests in test_*.py files
        if "test_" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "slow" in item.nodeid or "cache" in item.nodeid:
            item.add_marker(pytest.mark.slow)
