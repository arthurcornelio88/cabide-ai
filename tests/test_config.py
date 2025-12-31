"""
Tests for configuration management.
"""

import pytest

from src.config import Settings


def test_settings_defaults(test_env_vars):
    """Test that settings load with defaults."""
    settings = Settings()
    assert settings.gemini_api_key == "test_api_key_12345"
    assert settings.storage_mode == "local"
    assert settings.version == "1.1.0"


def test_settings_validation_storage_mode(test_env_vars, monkeypatch):
    """Test storage mode validation - always returns 'local'."""
    monkeypatch.setenv("STORAGE_MODE", "invalid")
    settings = Settings()
    # Storage mode is forced to 'local' by validator
    assert settings.storage_mode == "local"


def test_settings_validation_json(test_env_vars, monkeypatch):
    """Test JSON validation for service account."""
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", "{invalid json")
    with pytest.raises(ValueError, match="must be valid JSON"):
        Settings()


def test_settings_from_env(test_env_vars, monkeypatch):
    """Test loading Google Drive folder ID from environment."""
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "custom-folder-id-123")
    settings = Settings()
    assert settings.gdrive_folder_id == "custom-folder-id-123"
