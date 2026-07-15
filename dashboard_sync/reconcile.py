"""Reconciliacion de llamadas: re-escanea las ultimas N horas de llamadas de
Retell y procesa cualquier call_id que no este ya en la Sheet. Es el pipeline
de ingesta principal (poll), invocado tanto por el cron externo via el endpoint
POST /webhooks/reconcile como a mano: python -m dashboard_sync.reconcile"""

import asyncio
import time

import requests
from dotenv import load_dotenv

load_dotenv()

from dashboard_sync import config, pipeline, sheets_client

RETELL_LIST_CALLS_URL = "https://api.retellai.com/v2/list-calls"

# Retell tarda unos segundos a un par de minutos en terminar el post-call
# analysis (summary, sentiment, etc.) despues de que la llamada termina. Si
# reconcile sincroniza antes de eso, el call_id queda "synced" con esos
# campos vacios para siempre -- nadie lo vuelve a mirar. Mejor esperar una
# corrida mas (cron cada 15 min) en vez de congelar una fila incompleta.
ANALYSIS_GRACE_S = 600


def _analysis_ready(raw_call: dict) -> bool:
    return bool((raw_call.get("call_analysis") or {}).get("call_summary"))


def _should_defer(raw_call: dict) -> bool:
    if _analysis_ready(raw_call):
        return False
    end_ms = raw_call.get("end_timestamp")
    if not end_ms:
        return False
    age_s = (time.time() * 1000 - end_ms) / 1000
    return age_s < ANALYSIS_GRACE_S


def fetch_recent_calls(lookback_hours=None) -> list:
    if lookback_hours is None:
        lookback_hours = config.RECONCILE_LOOKBACK_HOURS
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - lookback_hours * 3600 * 1000
    headers = {
        "Authorization": f"Bearer {config.RETELL_API_KEY}",
        "Content-Type": "application/json",
    }

    all_calls = []
    pagination_key = None
    while True:
        payload = {
            "filter_criteria": {
                "start_timestamp": {
                    "op": "bt",
                    "type": "range",
                    "value": [start_ms, end_ms],
                }
            },
            "limit": 1000,
            "sort_order": "descending",
        }
        if pagination_key:
            payload["pagination_key"] = pagination_key

        response = requests.post(
            RETELL_LIST_CALLS_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            all_calls.extend(data)
            break

        items = data.get("items") or []
        all_calls.extend(items)
        if data.get("has_more") and data.get("pagination_key"):
            pagination_key = data["pagination_key"]
        else:
            break

    return all_calls


def filter_unsynced(calls: list, already_synced_ids: set) -> list:
    return [call for call in calls if call.get("call_id") and call["call_id"] not in already_synced_ids]


async def run(lookback_hours=None, sheets=None) -> dict:
    """Corre una pasada de reconciliacion y devuelve un resumen contable.
    `sheets` se puede inyectar para reutilizar el cliente singleton del endpoint
    (evita reconectar a Google en cada ping del cron); si es None, conecta uno."""
    if lookback_hours is None:
        lookback_hours = config.RECONCILE_LOOKBACK_HOURS
    if sheets is None:
        sheets = sheets_client.connect(
            sheet_id=config.GOOGLE_SHEET_ID,
            service_account_info=config.google_service_account_info(),
        )

    calls = fetch_recent_calls(lookback_hours)
    already_synced = set(sheets.get_existing_call_ids())
    pending = filter_unsynced(calls, already_synced)
    ready = [c for c in pending if not _should_defer(c)]
    deferred = len(pending) - len(ready)
    batch = ready[: config.RECONCILE_MAX_PER_RUN]
    print(
        f"[reconcile] {len(pending)} llamadas sin sincronizar de {len(calls)} "
        f"en las ultimas {lookback_hours}h ({deferred} con analisis pendiente, "
        f"procesando {len(batch)} esta corrida)"
    )

    synced = 0
    errors = 0
    for raw_call in batch:
        try:
            await pipeline.process_call(raw_call, sheets, config.BLOB_READ_WRITE_TOKEN)
            synced += 1
            print(f"[reconcile] OK {raw_call['call_id']}")
        except Exception as exc:
            errors += 1
            print(f"[reconcile] ERROR {raw_call.get('call_id')}: {exc}")

    return {
        "scanned": len(calls),
        "pending": len(pending),
        "synced": synced,
        "errors": errors,
        "deferred": deferred,
        "capped": len(ready) - len(batch),
    }


if __name__ == "__main__":
    asyncio.run(run())
