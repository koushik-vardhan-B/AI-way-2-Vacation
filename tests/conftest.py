import pytest
from fastapi.testclient import TestClient
from main import app
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["API_KEY"] = "test-api-key"
    os.environ["GOOGLE_API_KEY"] = "test-google-key"
    os.environ["GROQ_API_KEY"] = "test-groq-key"
    # Add other required test keys...
    yield
    # Cleanup if needed

@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)