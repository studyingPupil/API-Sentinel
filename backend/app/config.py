"""Application configuration. All values from environment variables."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "api_sentinel.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

DEFAULT_SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "60"))
DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "90"))

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
