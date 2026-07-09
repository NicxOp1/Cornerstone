"""Corrida unica: procesa los JSON de llamadas ya descargados en
'llamadas por dia/{mes}/{YYYY-MM-DD}/{call_id}.json' sin volver a pegarle a
la API de Retell. Uso: python -m dashboard_sync.backfill_calls"""

import asyncio
import json
from pathlib import Path
from typing import Iterator

from dashboard_sync import config, pipeline, sheets_client


def iter_local_call_files(base_dir: Path) -> Iterator[Path]:
    if not base_dir.exists():
        return

    for month_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        for day_dir in sorted(path for path in month_dir.iterdir() if path.is_dir()):
            for call_file in sorted(day_dir.glob("*.json")):
                yield call_file


async def run():
    sheets = sheets_client.connect(
        sheet_id=config.GOOGLE_SHEET_ID,
        service_account_info=config.google_service_account_info(),
    )
    base_dir = Path(config.CALLS_BACKFILL_DIR)

    total = 0
    errors = 0
    for call_file in iter_local_call_files(base_dir):
        try:
            raw_call = json.loads(call_file.read_text(encoding="utf-8"))
            await pipeline.process_call(raw_call, sheets, config.BLOB_READ_WRITE_TOKEN)
            total += 1
        except Exception as exc:
            errors += 1
            print(f"[backfill] ERROR {call_file.name}: {exc}")

    print(f"[backfill] Listo. {total} llamadas procesadas, {errors} errores.")


if __name__ == "__main__":
    asyncio.run(run())
