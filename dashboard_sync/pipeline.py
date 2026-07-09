"""Orquesta la normalizacion, blobs, booking_effectiveness y Sheets."""

import time

from dashboard_sync import blob_storage, booking_effectiveness, normalize


async def process_call(raw_call: dict, sheets, blob_token: str) -> dict:
    fields = normalize.extract(raw_call)
    call_id = fields["call_id"]

    try:
        if raw_call.get("recording_url"):
            fields["recording_blob_url"] = (
                blob_storage.upload_recording(call_id, raw_call["recording_url"], blob_token) or ""
            )
        else:
            fields["recording_blob_url"] = ""
    except Exception:
        fields["recording_blob_url"] = ""

    try:
        fields["transcript_blob_url"] = (
            blob_storage.upload_transcript(
                call_id,
                raw_call.get("transcript_with_tool_calls") or [],
                blob_token,
            )
            or ""
        )
    except Exception:
        fields["transcript_blob_url"] = ""

    try:
        fields["booking_effectiveness"] = await booking_effectiveness.check_call(raw_call)
    except Exception as exc:
        print(f"[dashboard_sync.pipeline] booking_effectiveness fallo para {call_id}: {exc}")
        fields["booking_effectiveness"] = "pending"

    fields["synced_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

    sheets.upsert_call_row(call_id, fields)
    return fields
