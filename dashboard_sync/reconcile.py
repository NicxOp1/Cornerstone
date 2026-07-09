"""Cron diario de reconciliacion: re-escanea las ultimas 48h de llamadas de
Retell y procesa cualquier call_id que el webhook se haya perdido. Uso:
python -m dashboard_sync.reconcile"""

import asyncio
import time

import requests

from dashboard_sync import config, pipeline, sheets_client

RETELL_LIST_CALLS_URL = "https://api.retellai.com/v2/list-calls"
DEFAULT_LOOKBACK_HOURS = 48


def fetch_recent_calls(lookback_hours: int = DEFAULT_LOOKBACK_HOURS) -> list:
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


async def run():
    sheets = sheets_client.connect(
        sheet_id=config.GOOGLE_SHEET_ID,
        service_account_info=config.google_service_account_info(),
    )

    calls = fetch_recent_calls()
    already_synced = set(sheets.get_existing_call_ids())
    pending = filter_unsynced(calls, already_synced)
    print(
        f"[reconcile] {len(pending)} llamadas sin sincronizar de {len(calls)} "
        f"en las ultimas {DEFAULT_LOOKBACK_HOURS}h"
    )

    for raw_call in pending:
        try:
            await pipeline.process_call(raw_call, sheets, config.BLOB_READ_WRITE_TOKEN)
            print(f"[reconcile] OK {raw_call['call_id']}")
        except Exception as exc:
            print(f"[reconcile] ERROR {raw_call.get('call_id')}: {exc}")


if __name__ == "__main__":
    asyncio.run(run())
