import io
import logging
import re
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger("DriveService")


class DriveService:
    def __init__(self, credentials, folder_id: str):
        """
        Initializes the Drive service using OAuth or Service Account credentials.

        Args:
            credentials: Google credentials object (from OAuth or Service Account)
            folder_id: Root folder ID in Google Drive
        """
        self.folder_id = folder_id
        self.creds = credentials
        self.service = build("drive", "v3", credentials=self.creds)
        self._folder_cache = {}  # Cache for folder IDs by date
        logger.info("DriveService initialized successfully")

    def _get_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """
        Get or create a folder by name inside a parent folder.
        Returns the folder ID.
        """
        # Search for existing folder with this name
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = (
            self.service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )

        folders = results.get("files", [])

        if folders:
            # Folder exists
            folder_id = folders[0]["id"]
            logger.info(f"Found existing folder: {folder_name} (ID: {folder_id})")
            return folder_id
        else:
            # Create new folder
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            folder = (
                self.service.files().create(body=folder_metadata, fields="id").execute()
            )
            folder_id = folder.get("id")
            logger.info(f"Created new folder: {folder_name} (ID: {folder_id})")
            return folder_id

    def _get_or_create_date_folder(self) -> str:
        """
        Get or create folder structure: YYYYMMDD/output/
        Returns the output folder ID.
        """
        today = datetime.now().strftime("%Y%m%d")

        # Check cache first
        cache_key = f"{today}/output"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        # Step 1: Create/get date folder (YYYYMMDD)
        date_folder_id = self._get_or_create_folder(today, self.folder_id)

        # Step 2: Create/get output folder inside date folder
        output_folder_id = self._get_or_create_folder("output", date_folder_id)

        # Cache the result
        self._folder_cache[cache_key] = output_folder_id
        return output_folder_id

    def _get_versioned_filename(self, folder_id: str, base_filename: str) -> str:
        """
        Check if filename exists in folder and return versioned name if needed.

        Examples:
            - cabide_100_vestido.png -> cabide_100_vestido.png (if doesn't exist)
            - cabide_100_vestido.png -> cabide_100_vestido_v1.png (if exists)
            - cabide_100_vestido.png -> cabide_100_vestido_v2.png (if v1 exists)
        """
        # Extract name and extension
        name_parts = base_filename.rsplit(".", 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
        else:
            base_name = base_filename
            extension = ""

        # Search for files with similar names in the folder
        # Pattern: base_name, base_name_v0, base_name_v1, etc.
        query = f"name contains '{base_name}' and '{folder_id}' in parents and trashed=false"
        results = (
            self.service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )

        existing_files = results.get("files", [])
        existing_names = [f["name"] for f in existing_files]

        # Check if base filename exists
        full_base_name = f"{base_name}.{extension}" if extension else base_name
        if full_base_name not in existing_names:
            # No conflict, use original name
            return base_filename

        # Find highest version number
        version_pattern = rf"{re.escape(base_name)}_v(\d+)\.{re.escape(extension)}"
        versions = []
        for name in existing_names:
            match = re.match(version_pattern, name)
            if match:
                versions.append(int(match.group(1)))

        # Determine next version
        if versions:
            next_version = max(versions) + 1
        else:
            next_version = 1

        # Return versioned filename
        versioned_name = (
            f"{base_name}_v{next_version}.{extension}"
            if extension
            else f"{base_name}_v{next_version}"
        )
        logger.info(f"File exists, using versioned name: {versioned_name}")
        return versioned_name

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        """
        Uploads an image buffer to the designated Google Drive folder.
        Automatically organizes by date and handles versioning.

        Args:
            file_bytes: Image bytes to upload
            filename: Base filename (e.g., 'cabide_100_vestido.png')

        Returns:
            webViewLink: URL to view the file in Google Drive
        """
        try:
            # Get or create today's date folder
            date_folder_id = self._get_or_create_date_folder()

            # Get versioned filename if needed
            final_filename = self._get_versioned_filename(date_folder_id, filename)

            # Upload file
            file_metadata = {"name": final_filename, "parents": [date_folder_id]}
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes), mimetype="image/png", resumable=True
            )

            file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id, webViewLink")
                .execute()
            )

            logger.info(
                f"File uploaded to Drive: {final_filename} (ID: {file.get('id')})"
            )
            return file.get("webViewLink")
        except Exception as e:
            logger.error(f"Drive upload failed: {e}")
            raise
