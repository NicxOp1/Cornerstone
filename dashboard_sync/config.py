# dashboard_sync/config.py
import json
import os

DASHBOARD_SYNC_TOKEN: str = os.environ.get("DASHBOARD_SYNC_TOKEN", "")
GOOGLE_SHEET_ID: str = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON: str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
BLOB_READ_WRITE_TOKEN: str = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
RETELL_API_KEY: str = os.environ.get("RETELL_API_KEY", "")
CALLS_BACKFILL_DIR: str = os.environ.get(
    "CALLS_BACKFILL_DIR", r"D:\ESCRITORIO\nex ia voice\llamadas por dia"
)


def google_service_account_info() -> dict:
    """Parsea el JSON del service account desde la env var. Se llama en cada
    conexión (no al importar el módulo) para que los tests puedan mockear
    GOOGLE_SERVICE_ACCOUNT_JSON sin recargar el módulo en producción."""
    return json.loads(GOOGLE_SERVICE_ACCOUNT_JSON) if GOOGLE_SERVICE_ACCOUNT_JSON else {}
