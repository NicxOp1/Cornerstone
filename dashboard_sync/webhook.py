"""FastAPI router for the dashboard_sync callSynced webhook."""

from fastapi import APIRouter, HTTPException, Request

from dashboard_sync import config, pipeline, sheets_client

router = APIRouter()

_sheets_singleton = None


def _get_sheets_client():
    global _sheets_singleton
    if _sheets_singleton is None:
        _sheets_singleton = sheets_client.connect(
            sheet_id=config.GOOGLE_SHEET_ID,
            service_account_info=config.google_service_account_info(),
        )
    return _sheets_singleton


def _extract_call_payload(body: dict) -> dict:
    call = body.get("call")
    if isinstance(call, dict) and call.get("call_id"):
        return call
    if body.get("call_id"):
        return body
    return {}


@router.post("/webhooks/callSynced")
async def call_synced(request: Request, token: str = ""):
    if token != config.DASHBOARD_SYNC_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    body = await request.json()
    raw_call = _extract_call_payload(body)
    call_id = raw_call.get("call_id")
    if not call_id:
        raise HTTPException(status_code=422, detail="No se pudo identificar call_id en el payload")

    try:
        await pipeline.process_call(raw_call, _get_sheets_client(), config.BLOB_READ_WRITE_TOKEN)
    except Exception:
        return {"status": "error", "call_id": call_id}

    return {"status": "ok", "call_id": call_id}
