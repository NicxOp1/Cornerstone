"""Orquesta la normalizacion, blobs, booking_effectiveness y Sheets."""

import asyncio
import time

from dashboard_sync import blob_storage, booking_effectiveness, normalize, office_alert


async def process_call(raw_call: dict, sheets, blob_token: str) -> dict:
    fields = normalize.extract(raw_call)
    call_id = fields["call_id"]

    # ¿Es la primera vez que sincronizamos esta llamada? Se chequea ANTES del
    # upsert para que el aviso del backstop se mande una sola vez (no en cada
    # re-proceso de la misma fila).
    is_new = not sheets.has_call(call_id)

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

    # Red de seguridad: si fue un intento de reserva con datos recolectados pero
    # sin create_job/reschedule exitoso, avisar a la oficina. Solo en la primera
    # sincronización (is_new) para no reenviar. No fatal: nunca romper la ingesta.
    if is_new:
        try:
            # En hilo aparte: dashboard_sync corre en el MISMO proceso FastAPI
            # que los endpoints de voz; un SMTP síncrono bloquearía el event loop
            # y demoraría las tool-responses de Harmony en una llamada en vivo.
            await asyncio.to_thread(office_alert.send_backstop_alert, raw_call, fields)
        except Exception as exc:
            print(f"[dashboard_sync.pipeline] backstop falló para {call_id}: {exc}")

    return fields
