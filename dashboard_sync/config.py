# dashboard_sync/config.py
import json
import os
from pathlib import Path

DASHBOARD_SYNC_TOKEN: str = os.environ.get("DASHBOARD_SYNC_TOKEN", "")
GOOGLE_SHEET_ID: str = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON: str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
BLOB_READ_WRITE_TOKEN: str = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
RETELL_API_KEY: str = os.environ.get("RETELL_API_KEY", "")

# Ventana que mira el reconcile en cada corrida. Debe cubrir como minimo los
# ultimos 15 dias para que las llamadas de julio no queden afuera del dashboard
# ni del backfill de Tools. Se puede ampliar por env para un backfill mayor.
MIN_RECONCILE_LOOKBACK_HOURS: int = 15 * 24
RECONCILE_LOOKBACK_HOURS: int = max(
    MIN_RECONCILE_LOOKBACK_HOURS,
    int(os.environ.get("RECONCILE_LOOKBACK_HOURS", str(MIN_RECONCILE_LOOKBACK_HOURS))),
)

# Tope de llamadas pendientes procesadas por corrida. Cada llamada pendiente
# puede pegarle a Retell (audio), Vercel Blob y ServiceTitan de forma
# secuencial -- sin tope, una racha de llamadas sin sincronizar hace que la
# corrida tarde varios minutos y el proxy de Render corte la conexion (esto
# tumbo el cron de GitHub Actions el 2026-07-14: "All jobs have failed" en
# ping-reconcile). El resto de las pendientes las agarra la proxima corrida
# del cron (cada 15 min) -- el pipeline es idempotente, no se pierde nada.
RECONCILE_MAX_PER_RUN: int = int(os.environ.get("RECONCILE_MAX_PER_RUN", "10"))

# Default calculado desde la ubicacion del repo (…/nex ia voice/llamadas por dia),
# no una ruta hardcodeada de una maquina puntual. Overridable por env.
_DEFAULT_BACKFILL_DIR = Path(__file__).resolve().parents[3] / "llamadas por dia"
CALLS_BACKFILL_DIR: str = os.environ.get("CALLS_BACKFILL_DIR", str(_DEFAULT_BACKFILL_DIR))


def google_service_account_info() -> dict:
    """Parsea el JSON del service account desde la env var. Se llama en cada
    conexión (no al importar el módulo) para que los tests puedan mockear
    GOOGLE_SERVICE_ACCOUNT_JSON sin recargar el módulo en producción."""
    return json.loads(GOOGLE_SERVICE_ACCOUNT_JSON) if GOOGLE_SERVICE_ACCOUNT_JSON else {}
