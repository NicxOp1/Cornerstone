# dashboard_sync/config.py
import json
import os
from pathlib import Path

DASHBOARD_SYNC_TOKEN: str = os.environ.get("DASHBOARD_SYNC_TOKEN", "")
GOOGLE_SHEET_ID: str = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON: str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
BLOB_READ_WRITE_TOKEN: str = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
RETELL_API_KEY: str = os.environ.get("RETELL_API_KEY", "")

# Ventana que mira el reconcile en cada corrida. Con el cron cada 10 min alcanza
# con unas pocas horas de solape (resiliente ante corridas perdidas) en vez de
# las 48h del cron diario original. Overridable por env para el backfill/diario.
RECONCILE_LOOKBACK_HOURS: int = int(os.environ.get("RECONCILE_LOOKBACK_HOURS", "3"))

# Default calculado desde la ubicacion del repo (…/nex ia voice/llamadas por dia),
# no una ruta hardcodeada de una maquina puntual. Overridable por env.
_DEFAULT_BACKFILL_DIR = Path(__file__).resolve().parents[3] / "llamadas por dia"
CALLS_BACKFILL_DIR: str = os.environ.get("CALLS_BACKFILL_DIR", str(_DEFAULT_BACKFILL_DIR))


def google_service_account_info() -> dict:
    """Parsea el JSON del service account desde la env var. Se llama en cada
    conexión (no al importar el módulo) para que los tests puedan mockear
    GOOGLE_SERVICE_ACCOUNT_JSON sin recargar el módulo en producción."""
    return json.loads(GOOGLE_SERVICE_ACCOUNT_JSON) if GOOGLE_SERVICE_ACCOUNT_JSON else {}
