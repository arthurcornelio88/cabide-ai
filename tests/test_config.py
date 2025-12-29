"""
Tests for configuration management.
"""
import pytest
import json
from src.config import Settings, get_settings


def test_settings_defaults(test_env_vars):
    """Test that settings load with defaults."""
    settings = Settings()
    assert settings.gemini_api_key == "test_api_key_12345"
    assert settings.storage_mode == "local"
    assert settings.version == "1.1.0"


def test_settings_validation_storage_mode(test_env_vars, monkeypatch):
    """Test storage mode validation."""
    monkeypatch.setenv("STORAGE_MODE", "invalid")
    with pytest.raises(ValueError, match="storage_mode must be"):
        Settings()


def test_settings_validation_json(test_env_vars, monkeypatch):
    """Test JSON validation for service account."""
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", "{invalid json")
    with pytest.raises(ValueError, match="must be valid JSON"):
        Settings()


def test_settings_from_env(test_env_vars, monkeypatch):
    """Test loading from environment variables."""
    monkeypatch.setenv("GCS_BUCKET_NAME", "custom-bucket")
    settings = Settings()
    assert settings.gcs_bucket_name == "custom-bucket"
