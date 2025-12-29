"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from io import BytesIO

from src.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint_returns_200(client, test_env_vars):
    """Test health check endpoint returns 200."""
    with patch('src.api.genai.configure'):
        with patch('src.api.genai.list_models', return_value=[]):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["model"] == "gemini-3-pro-image-preview"


def test_generate_endpoint_rejects_invalid_file_type(client, test_env_vars):
    """Test generate endpoint rejects invalid file types."""
    files = {'file': ('test.txt', BytesIO(b'not an image'), 'text/plain')}
    response = client.post("/generate", files=files)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_generate_endpoint_requires_filename(client, test_env_vars):
    """Test generate endpoint requires filename."""
    # FastAPI validation will catch this
    response = client.post("/generate")

    assert response.status_code == 422  # Validation error
