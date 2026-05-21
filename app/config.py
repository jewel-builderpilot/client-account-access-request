import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    WTF_CSRF_ENABLED = True

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

    GMAIL_CLIENT_ID = os.environ.get("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET = os.environ.get("GMAIL_CLIENT_SECRET", "")
    GMAIL_REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN", "")
    GMAIL_SENDER_EMAIL = os.environ.get("GMAIL_SENDER_EMAIL", "")

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")


class DevelopmentConfig(Config):
    DEBUG = True
    # Disable HTTPS enforcement locally
    TALISMAN_FORCE_HTTPS = False


class ProductionConfig(Config):
    DEBUG = False
    # Vercel terminates TLS at the edge — don't force HTTPS inside the container
    TALISMAN_FORCE_HTTPS = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
