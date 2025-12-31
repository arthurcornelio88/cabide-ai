"""
Pytest fixtures for Cabide AI tests.
"""

from io import BytesIO

import pytest
from PIL import Image


@pytest.fixture
def test_env_vars(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("STORAGE_MODE", "local")
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "test_folder_id")
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", "{}")


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = Image.new("RGB", (100, 100), color="red")
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Get sample image as bytes."""
    buffer = BytesIO()
    sample_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_image_file(tmp_path, sample_image):
    """Save sample image to temp file."""
    file_path = tmp_path / "test_garment.png"
    sample_image.save(file_path)
    return file_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir
