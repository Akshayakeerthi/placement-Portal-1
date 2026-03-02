import os
from datetime import timedelta


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'placement.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "uploads"))
    EXPORT_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "exports"))
    REPORT_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "reports"))

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@placement.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
    ADMIN_NAME = os.getenv("ADMIN_NAME", "System Admin")
