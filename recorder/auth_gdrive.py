"""Authorize the storage account: python recorder/auth_gdrive.py.

Enable Drive API in the shared OAuth project first. Testing-mode consent may
produce short-lived refresh tokens. This script never edits .env or YouTube
credentials. Its refresh-token output is a secret; do not commit or log it.
"""

import os
import sys
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recorder.src.gdrive.client import SCOPES, DriveClient  # noqa: E402


def main():
    # Process environment wins, then recorder settings, then root defaults.
    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    client_id = (
        os.environ.get("REC_GOOGLE_CLIENT_ID") or input("GOOGLE_CLIENT_ID: ").strip()
    )
    client_secret = (
        os.environ.get("REC_GOOGLE_CLIENT_SECRET")
        or getpass("GOOGLE_CLIENT_SECRET: ").strip()
    )
    if not client_id or not client_secret:
        raise SystemExit("Shared Google OAuth client credentials are required")
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        SCOPES,
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        open_browser=True,
        access_type="offline",
        prompt="consent select_account",
    )
    if not credentials.refresh_token:
        raise SystemExit("No refresh token returned; repeat authorization with consent")
    client = DriveClient(
        build("drive", "v3", credentials=credentials, cache_discovery=False)
    )
    root = client.ensure_root()
    print(f"\nPrivate Drive archive root verified: {root['id']}")
    print("Save this secret in .env (leave REC_YOUTUBE_REFRESH_TOKEN unchanged):\n")
    print(f"REC_GDRIVE_REFRESH_TOKEN={credentials.refresh_token}")


if __name__ == "__main__":
    main()
