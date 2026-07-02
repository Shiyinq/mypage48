"""
One-time OAuth script to get YouTube refresh token.

Usage:
  python recorder/auth_youtube.py

You will be prompted to open a URL in your browser.
After authorizing, paste the redirect URL or authorization code.

Output: refresh token to paste in .env as REC_YOUTUBE_REFRESH_TOKEN
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")  # root .env
load_dotenv(Path(__file__).parent / ".env")  # recorder/.env

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = (
    os.environ.get("REC_GOOGLE_CLIENT_ID") or input("GOOGLE_CLIENT_ID: ").strip()
)
CLIENT_SECRET = (
    os.environ.get("REC_GOOGLE_CLIENT_SECRET")
    or input("GOOGLE_CLIENT_SECRET: ").strip()
)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
flow.run_local_server(open_browser=True, port=8080)

print("\n=== Save these in .env ===\n")
print(f"REC_GOOGLE_CLIENT_ID={CLIENT_ID}")
print(f"REC_GOOGLE_CLIENT_SECRET={CLIENT_SECRET}")
print(f"REC_YOUTUBE_REFRESH_TOKEN={flow.credentials.refresh_token}")
print()
