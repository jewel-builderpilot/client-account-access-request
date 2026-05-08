"""
One-time script to get a Gmail OAuth2 refresh token.

Before running:
1. Go to console.cloud.google.com → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Desktop app)
3. Download the JSON and note the client_id and client_secret

Usage:
    python scripts/get_gmail_token.py

It will open your browser to authorize Gmail sending access.
Copy the printed refresh token into your .env as GMAIL_REFRESH_TOKEN.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    print("\n=== Gmail OAuth2 Token Generator ===\n")
    client_id = input("Paste your GMAIL_CLIENT_ID: ").strip()
    client_secret = input("Paste your GMAIL_CLIENT_SECRET: ").strip()

    if not client_id or not client_secret:
        print("Error: client_id and client_secret are required.")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    print("\n✅ Authorization successful!\n")
    print("Add these to your .env file:")
    print(f"  GMAIL_CLIENT_ID={client_id}")
    print(f"  GMAIL_CLIENT_SECRET={client_secret}")
    print(f"  GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print(f"  GMAIL_SENDER_EMAIL=<the Gmail address you just authorized>")
    print()


if __name__ == "__main__":
    main()
