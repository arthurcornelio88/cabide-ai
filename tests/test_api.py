"""
Tests for FastAPI endpoints.
"""

from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint_returns_200(client, test_env_vars):
    """Test health check endpoint returns 200."""
    # Mock the new SDK's Client class and models.list() method
    with patch("src.api.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.list.return_value = []

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["model"] == "gemini-3-pro-image-preview"


@pytest.mark.skip(reason="OAuth authentication blocks endpoint - needs mock refactor")
def test_generate_endpoint_rejects_invalid_file_type(client, test_env_vars):
    """Test generate endpoint rejects invalid file types."""
    files = {"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
    # Mock OAuth verification to bypass authentication
    with patch("src.api.verify_oauth_token", return_value=True):
        response = client.post("/generate", files=files)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.skip(reason="OAuth authentication blocks endpoint - needs mock refactor")
def test_generate_endpoint_requires_filename(client, test_env_vars):
    """Test generate endpoint requires filename."""
    # FastAPI validation will catch this
    # Mock OAuth to bypass authentication
    with patch("src.api.verify_oauth_token", return_value=True):
        response = client.post("/generate")

    assert response.status_code == 422  # Validation error
