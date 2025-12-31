"""
Unified OAuth helper for Google authentication.
Handles user authentication flow and token management for both Drive and API access.
"""

import json
import os
import pickle
import tempfile
from pathlib import Path
from typing import Dict, Optional

import google.auth.exceptions
import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


class UnifiedOAuthHelper:
    """Manages unified OAuth authentication for Google services."""

    # Scopes for both Drive access and user info
    SCOPES = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]
    # Fallback for local development (when Streamlit is not available)
    TOKEN_FILE = Path("auth_token.pickle")
    USER_INFO_FILE = Path("user_info.json")

    def __init__(self, client_secrets_file: str = "client_secret.json"):
        """
        Initialize OAuth helper.

        Args:
            client_secrets_file: Path to OAuth client secrets JSON file
        """
        # SECURITY: Clean up any existing credential files on Streamlit Cloud
        # This prevents credentials from being shared between users
        if HAS_STREAMLIT and hasattr(st, "secrets"):
            try:
                # Remove old files that might exist from previous sessions
                if self.TOKEN_FILE.exists():
                    os.remove(self.TOKEN_FILE)
                if self.USER_INFO_FILE.exists():
                    os.remove(self.USER_INFO_FILE)
            except Exception:
                pass  # Ignore errors during cleanup

        # Try to get client secrets from Streamlit Cloud secrets first
        using_secrets = False
        if HAS_STREAMLIT:
            try:
                if hasattr(st, "secrets") and "CLIENT_SECRET_JSON" in st.secrets:
                    # Create a temporary file with the secrets content
                    client_secret_data = json.loads(st.secrets["CLIENT_SECRET_JSON"])

                    # Write to a temporary file that Flow can read
                    self._temp_file = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".json", delete=False
                    )
                    json.dump(client_secret_data, self._temp_file)
                    self._temp_file.close()
                    self.client_secrets_file = self._temp_file.name
                    using_secrets = True
            except Exception:
                # If secrets access fails, fall back to local file
                pass

        if not using_secrets:
            # Use local file path
            self.client_secrets_file = client_secrets_file
            self._temp_file = None

    def get_credentials(self) -> Optional[Credentials]:
        """
        Get valid user credentials from storage.

        Returns:
            Credentials object or None if not authenticated
        """
        creds = None

        # Use session_state in Streamlit Cloud, fallback to file storage locally
        if HAS_STREAMLIT and hasattr(st, "session_state"):
            # Check session state first (isolated per user session)
            if "oauth_credentials" in st.session_state:
                creds = st.session_state.oauth_credentials
        else:
            # Fallback to file storage for local development
            if self.TOKEN_FILE.exists():
                with open(self.TOKEN_FILE, "rb") as token:
                    creds = pickle.load(token)

        # If credentials are invalid or don't exist, refresh or get new ones
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                if HAS_STREAMLIT and hasattr(st, "session_state"):
                    st.session_state.oauth_credentials = creds
                else:
                    with open(self.TOKEN_FILE, "wb") as token:
                        pickle.dump(creds, token)
            except google.auth.exceptions.RefreshError:
                # Token refresh failed - user needs to re-authenticate
                return None

        return creds if (creds and creds.valid) else None

    def get_user_info(self) -> Optional[Dict]:
        """
        Get cached user information.

        Returns:
            Dict with user info (email, name, picture) or None
        """
        # Use session_state in Streamlit Cloud, fallback to file storage locally
        if HAS_STREAMLIT and hasattr(st, "session_state"):
            return st.session_state.get("oauth_user_info")
        else:
            # Fallback to file storage for local development
            if self.USER_INFO_FILE.exists():
                with open(self.USER_INFO_FILE, "r") as f:
                    return json.load(f)
        return None

    def fetch_and_save_user_info(self, creds: Credentials) -> Dict:
        """
        Fetch user info from Google and save it locally.

        Args:
            creds: Valid credentials object

        Returns:
            Dict with user info
        """
        import requests

        headers = {"Authorization": f"Bearer {creds.token}"}
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo", headers=headers
        )
        response.raise_for_status()
        user_info = response.json()

        # Save user info - use session_state in Streamlit, file storage locally
        if HAS_STREAMLIT and hasattr(st, "session_state"):
            st.session_state.oauth_user_info = user_info
        else:
            with open(self.USER_INFO_FILE, "w") as f:
                json.dump(user_info, f, indent=2)

        return user_info

    def get_auth_url(self, redirect_uri: Optional[str] = None) -> tuple:
        """
        Get OAuth authorization URL for user to visit.

        Args:
            redirect_uri: Custom redirect URI. If None, uses http://localhost:8080

        Returns:
            tuple: (authorization_url, flow_state)
        """
        if redirect_uri is None:
            redirect_uri = "http://localhost:8080"

        flow = Flow.from_client_secrets_file(
            self.client_secrets_file, scopes=self.SCOPES, redirect_uri=redirect_uri
        )

        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent screen to get refresh token
        )

        return auth_url, flow

    def save_credentials_from_code(self, flow: Flow, code: str) -> Credentials:
        """
        Exchange authorization code for credentials and save them.

        Args:
            flow: OAuth flow object from get_auth_url()
            code: Authorization code from user

        Returns:
            Credentials object
        """
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save credentials - use session_state in Streamlit, file storage locally
        if HAS_STREAMLIT and hasattr(st, "session_state"):
            st.session_state.oauth_credentials = creds
        else:
            with open(self.TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        # Fetch and save user info
        self.fetch_and_save_user_info(creds)

        return creds

    def run_local_server_flow(self, port: int = 8080) -> Credentials:
        """
        Run OAuth flow with local server (easier for users).
        Opens browser automatically and catches the redirect.

        Args:
            port: Local port for redirect server

        Returns:
            Credentials object
        """
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, scopes=self.SCOPES
        )

        # Run local server and get credentials
        creds = flow.run_local_server(
            port=port, access_type="offline", prompt="consent"
        )

        # Save credentials - use session_state in Streamlit, file storage locally
        if HAS_STREAMLIT and hasattr(st, "session_state"):
            st.session_state.oauth_credentials = creds
        else:
            with open(self.TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        # Fetch and save user info
        self.fetch_and_save_user_info(creds)

        return creds

    def get_access_token(self) -> Optional[str]:
        """
        Get current access token for API authentication.

        Returns:
            Access token string or None if not authenticated
        """
        creds = self.get_credentials()
        return creds.token if creds else None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        creds = self.get_credentials()
        return creds is not None and creds.valid

    def revoke_authentication(self):
        """Remove stored credentials."""
        # Clear session_state in Streamlit, file storage locally
        if HAS_STREAMLIT and hasattr(st, "session_state"):
            # Clear OAuth session data
            if "oauth_credentials" in st.session_state:
                del st.session_state.oauth_credentials
            if "oauth_user_info" in st.session_state:
                del st.session_state.oauth_user_info
        else:
            # Fallback to file storage for local development
            if self.TOKEN_FILE.exists():
                os.remove(self.TOKEN_FILE)
            if self.USER_INFO_FILE.exists():
                os.remove(self.USER_INFO_FILE)

    def __del__(self):
        """Cleanup temporary file if created."""
        if hasattr(self, "_temp_file") and self._temp_file is not None:
            try:
                os.unlink(self._temp_file.name)
            except Exception:
                pass  # Ignore errors during cleanup
