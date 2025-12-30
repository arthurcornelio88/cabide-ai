"""
Centralized configuration management for Cabide AI.
Uses Pydantic v2 settings with proper environment variable handling.
"""
import json
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Unified settings for Cabide AI.
    Handles all configuration for engine, API, frontend, and batch processing.
    """
    # API Keys
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")

    # Storage Configuration
    storage_mode: str = Field(default="local", validation_alias="STORAGE_MODE")
    gcs_bucket_name: str = Field(default="cabide-catalog-br", validation_alias="GCS_BUCKET_NAME")

    # Google Drive Integration
    gdrive_folder_id: str = Field(default="", validation_alias="GDRIVE_FOLDER_ID")
    gcp_service_account_json: str = Field(default="{}", validation_alias="GCP_SERVICE_ACCOUNT_JSON")
    gdrive_user_email: str = Field(default="", validation_alias="GDRIVE_USER_EMAIL")  # Email to impersonate

    # Paths
    output_dir: Path = Field(default=Path("img/gen_images/output"))
    temp_upload_dir: Path = Field(default=Path("temp/uploads"))
    templates_file: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "PROMPT_TEMPLATES.md")

    # Batch Processing Defaults
    input_dir: Path = Field(default=Path("img/gen_images/input"))

    # Global random pools for batch processing
    environments: List[str] = Field(default=[
        "forest", "park", "beach", "urban street", "luxury hotel",
        "office", "congress hall", "medical office"
    ])
    activities: List[str] = Field(default=[
        "walking", "checking phone", "holding a coffee", "smiling at the camera",
        "giving a presentation", "attending to a client"
    ])

    # API Configuration
    backend_url: Optional[str] = Field(default=None, validation_alias="BACKEND_URL")

    # Version
    version: str = "1.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    @field_validator("storage_mode")
    @classmethod
    def validate_storage_mode(cls, v: str) -> str:
        if v not in ["local", "prod"]:
            raise ValueError("storage_mode must be 'local' or 'prod'")
        return v

    @field_validator("gcp_service_account_json")
    @classmethod
    def validate_json(cls, v: str) -> str:
        """Ensure the JSON is parseable if not empty"""
        if v and v != "{}":
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("gcp_service_account_json must be valid JSON")
        return v

    def get_service_account_info(self) -> Optional[dict]:
        """
        Load GCP service account credentials with fallback logic:
        1. Try environment variable GCP_SERVICE_ACCOUNT_JSON (for prod/Docker)
        2. Try reading from gcp-service-account.json file (for local dev)
        3. Return None if neither exists

        This works in both local and production without code changes.
        """
        # Priority 1: Environment variable (prod/Docker)
        if self.gcp_service_account_json and self.gcp_service_account_json != "{}":
            try:
                return json.loads(self.gcp_service_account_json)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in GCP_SERVICE_ACCOUNT_JSON env var: {e}")

        # Priority 2: Local file (dev)
        service_account_file = Path("gcp-service-account.json")
        if service_account_file.exists():
            try:
                with open(service_account_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load gcp-service-account.json: {e}")

        # No credentials found
        return None


# Singleton pattern for settings
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
