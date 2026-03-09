import os
from datetime import timedelta
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    ROOT_DIR = BASE_DIR.parent

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'placement.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-jwt-key-please-use-32-bytes-minimum")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    UPLOAD_FOLDER = str(ROOT_DIR / "uploads")
    EXPORT_FOLDER = str(ROOT_DIR / "exports")
    REPORT_FOLDER = str(ROOT_DIR / "reports")

    ADMIN_NAME = os.getenv("ADMIN_NAME", "Placement Admin")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ppa.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

    MAIL_FROM = os.getenv("MAIL_FROM", "noreply@ppa.local")
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", "0") == "1"
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "0") == "1"
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    CHAT_WEBHOOK_URL = os.getenv("CHAT_WEBHOOK_URL", "")
