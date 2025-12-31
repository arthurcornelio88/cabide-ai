"""
API Client for Cabide AI Frontend.
Handles communication between Streamlit UI and FastAPI backend.
"""

from typing import BinaryIO, Optional

import requests

from src.config import get_settings


class CabideAPIClient:
    """Client for interacting with Cabide AI FastAPI backend."""

    def __init__(
        self, base_url: Optional[str] = None, access_token: Optional[str] = None
    ):
        """
        Initialize API client.

        Args:
            base_url: Backend URL. If None, uses BACKEND_URL from settings.
            access_token: OAuth access token for authentication.
        """
        settings = get_settings()
        self.base_url = base_url or settings.backend_url or "http://localhost:8000"
        self.base_url = self.base_url.rstrip("/")
        self.access_token = access_token

        # Prepare headers with authentication
        self.headers = {}
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    def health_check(self) -> dict:
        """
        Check if backend is healthy.

        Returns:
            Health check response with status, model, storage_mode, version

        Raises:
            requests.RequestException: If request fails
        """
        response = requests.get(
            f"{self.base_url}/health", headers=self.headers, timeout=5
        )
        response.raise_for_status()
        return response.json()

    def generate_photo(
        self,
        image_files: list[tuple[str, BinaryIO]] | tuple[str, BinaryIO],
        environment: str = "street",
        activity: str = "posing for a lifestyle catalog",
        garment_number: str = None,
        garment_type: str = None,
        position: str = None,
        feedback: str = None,
        piece1_type: str = None,
        piece2_type: str = None,
        piece3_type: str = None,
    ) -> dict:
        """
        Generate lifestyle photo via backend API.

        Args:
            image_files: List of (filename, file_object) tuples or single tuple
            environment: Scene environment
            activity: Model activity (currently ignored by backend, reserved)
            garment_number: Garment number
            garment_type: Garment type
            position: Photo position (front/back)
            feedback: User feedback for regeneration
            piece1_type: For conjunto - upper piece type
            piece2_type: For conjunto - lower piece type
            piece3_type: For conjunto - additional piece type (optional)

        Returns:
            dict with 'url' (in prod mode) or 'image_bytes' (in local mode)

        Raises:
            requests.RequestException: If request fails
        """
        # Handle both single file and multiple files
        if not isinstance(image_files, list):
            image_files = [image_files]

        # Prepare files for upload
        files = [
            ("files", (filename, file_obj, "image/png"))
            for filename, file_obj in image_files
        ]

        data = {"env": environment}

        # Add metadata if provided
        if garment_number:
            data["garment_number"] = garment_number
        if garment_type:
            data["garment_type"] = garment_type
        if position:
            data["position"] = position
        if feedback:
            data["feedback"] = feedback
        if piece1_type:
            data["piece1_type"] = piece1_type
        if piece2_type:
            data["piece2_type"] = piece2_type
        if piece3_type:
            data["piece3_type"] = piece3_type

        response = requests.post(
            f"{self.base_url}/generate",
            files=files,
            data=data,
            headers=self.headers,
            timeout=180,  # 3 minutes - Gemini can take time, especially for conjuntos
        )
        response.raise_for_status()

        # Handle both JSON response (prod) and file response (local)
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            return response.json()
        else:
            # Local mode returns image file
            return {"image_bytes": response.content, "content_type": content_type}
