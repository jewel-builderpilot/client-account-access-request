"""Gmail API email sender using OAuth2 refresh token."""
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def _get_gmail_service():
    creds = Credentials(
        token=None,
        refresh_token=current_app.config["GMAIL_REFRESH_TOKEN"],
        client_id=current_app.config["GMAIL_CLIENT_ID"],
        client_secret=current_app.config["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email via Gmail API. Returns True on success."""
    sender = current_app.config.get("GMAIL_SENDER_EMAIL", "")
    if not all([
        current_app.config.get("GMAIL_CLIENT_ID"),
        current_app.config.get("GMAIL_CLIENT_SECRET"),
        current_app.config.get("GMAIL_REFRESH_TOKEN"),
        sender,
    ]):
        current_app.logger.warning("Gmail API not configured — email not sent.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        service = _get_gmail_service()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except HttpError as exc:
        current_app.logger.error(f"Gmail API error: {exc}")
        return False
    except Exception as exc:
        current_app.logger.error(f"Gmail send error: {exc}")
        return False
