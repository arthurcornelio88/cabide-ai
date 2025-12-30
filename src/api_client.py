"""
API Client for Cabide AI Frontend.
Handles communication between Streamlit UI and FastAPI backend.
"""
import requests
from typing import Optional, BinaryIO
from src.config import get_settings


class CabideAPIClient:
    """Client for interacting with Cabide AI FastAPI backend."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.

        Args:
            base_url: Backend URL. If None, uses BACKEND_URL from settings.
        """
        settings = get_settings()
        self.base_url = base_url or settings.backend_url or "http://localhost:8000"
        self.base_url = self.base_url.rstrip("/")

    def health_check(self) -> dict:
        """
        Check if backend is healthy.

        Returns:
            Health check response with status, model, storage_mode, version

        Raises:
            requests.RequestException: If request fails
        """
        response = requests.get(f"{self.base_url}/health", timeout=5)
        response.raise_for_status()
        return response.json()

    def generate_photo(
        self,
        image_file: BinaryIO,
        filename: str,
        environment: str = "street",
        activity: str = "posing for a lifestyle catalog",
        garment_number: str = None,
        garment_type: str = None,
        position: str = None,
        feedback: str = None
    ) -> dict:
        """
        Generate lifestyle photo via backend API.

        Args:
            image_file: File-like object containing image bytes
            filename: Original filename
            environment: Scene environment
            activity: Model activity (currently ignored by backend, reserved)

        Returns:
            dict with 'url' (in prod mode) or 'image_bytes' (in local mode)

        Raises:
            requests.RequestException: If request fails
        """
        files = {'file': (filename, image_file, 'image/png')}
        data = {'env': environment}

        # Add metadata if provided
        if garment_number:
            data['garment_number'] = garment_number
        if garment_type:
            data['garment_type'] = garment_type
        if position:
            data['position'] = position
        if feedback:
            data['feedback'] = feedback

        response = requests.post(
            f"{self.base_url}/generate",
            files=files,
            data=data,
            timeout=60  # Gemini can take time
        )
        response.raise_for_status()

        # Handle both JSON response (prod) and file response (local)
        content_type = response.headers.get('content-type', '')

        if 'application/json' in content_type:
            return response.json()
        else:
            # Local mode returns image file
            return {
                'image_bytes': response.content,
                'content_type': content_type
            }
