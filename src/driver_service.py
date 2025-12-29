import io
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

logger = logging.getLogger("DriveService")

class DriveService:
    def __init__(self, service_account_info: dict, folder_id: str):
        """
        Initializes the Drive service using Service Account credentials.
        """
        self.folder_id = folder_id
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        self.creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=self.scopes
        )
        self.service = build('drive', 'v3', credentials=self.creds)

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        """
        Uploads an image buffer to the designated Google Drive folder.
        """
        try:
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes),
                mimetype='image/png',
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            logger.info(f"File uploaded to Drive. ID: {file.get('id')}")
            return file.get('webViewLink')
        except Exception as e:
            logger.error(f"Drive upload failed: {e}")
            raise
