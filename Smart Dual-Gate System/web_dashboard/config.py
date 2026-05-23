import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


class Config:
    PROJECT_ROOT = PROJECT_ROOT
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key-in-production")
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        str(PROJECT_ROOT / "database" / "mantrap.db"),
    )
    STATUS_FILE_PATH = os.environ.get(
        "STATUS_FILE_PATH",
        str(PROJECT_ROOT / "runtime" / "mantrap_status.json"),
    )
    SYSTEM_LOG_PATH = os.environ.get(
        "SYSTEM_LOG_PATH",
        str(PROJECT_ROOT / "logs" / "system.log"),
    )
    YOLO_STREAM_BASE_URL = os.environ.get(
        "YOLO_STREAM_BASE_URL",
        "http://127.0.0.1:5000",
    ).rstrip("/")

    DASHBOARD_HOST = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8000"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    PERMANENT_SESSION_LIFETIME_HOURS = int(
        os.environ.get("PERMANENT_SESSION_LIFETIME_HOURS", "12")
    )

    STATUS_STALE_SECONDS = int(os.environ.get("STATUS_STALE_SECONDS", "15"))
    STREAM_HEALTH_TIMEOUT = float(os.environ.get("STREAM_HEALTH_TIMEOUT", "2.0"))

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    DEFAULT_PAGE_SIZE = 25
