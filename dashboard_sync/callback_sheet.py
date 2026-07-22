"""Escribe los callbacks (transferencias fallidas, pedidos de mensaje/callback)
directo en la Google Sheet principal (GOOGLE_SHEET_ID), tabs "Emergency" /
"Non-Emergency" -- reemplaza al webhook de Make.com que escribia en una sheet
aparte. El dashboard ya lee de esas dos tabs con este mismo schema
(dashboard/lib/data/callbacks-repository.ts) -- antes apuntaba a una sheet
separada via CALLBACKS_SHEET_ID, ahora los datos quedan en la sheet central.
Ver docs/2026-07-18-plan-implementacion-qa.md (migracion de callbacks)."""

import time

from dashboard_sync import config

TAB_BY_EMERGENCY = {True: "Emergency", False: "Non-Emergency"}

# Headers exactos que espera dashboard/lib/data/callbacks-repository.ts.
CALLBACK_HEADERS = [
    "Timestamp", "Status", "Full Name", "Phone Number",
    "Reason for Call", "Preferred Callback Time", "Email (optional)", "Call Id",
]

_worksheet_cache: dict = {}


def _get_worksheet(tab_name: str):
    if tab_name in _worksheet_cache:
        return _worksheet_cache[tab_name]
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        config.google_service_account_info(),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(config.GOOGLE_SHEET_ID).worksheet(tab_name)
    _worksheet_cache[tab_name] = worksheet
    return worksheet


def append_callback(name, number, reason, callback, is_emergency, email, call_id) -> None:
    """Agrega una fila de callback. Idempotente por Call Id: si Retell reintenta
    el mismo tool call (mismo call_id), actualiza la fila existente en vez de
    duplicarla -- mismo criterio que upsert_call_row en sheets_client.py."""
    tab = TAB_BY_EMERGENCY.get(bool(is_emergency), "Non-Emergency")
    worksheet = _get_worksheet(tab)
    headers = worksheet.row_values(1) or CALLBACK_HEADERS

    record = {
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "Status": "",
        "Full Name": name or "",
        "Phone Number": number or "",
        "Reason for Call": reason or "",
        "Preferred Callback Time": callback or "",
        "Email (optional)": email or "",
        "Call Id": call_id or "",
    }
    row = [str(record.get(h, "")) for h in headers]

    if call_id and "Call Id" in headers:
        id_col = headers.index("Call Id") + 1
        existing_ids = worksheet.col_values(id_col)
        for row_number, value in enumerate(existing_ids[1:], start=2):
            if value == call_id:
                worksheet.update(f"A{row_number}", [row])
                return

    worksheet.append_row(row, value_input_option="RAW")
