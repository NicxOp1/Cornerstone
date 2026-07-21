"""FastAPI router for the dashboard_sync callSynced webhook y el endpoint de
reconciliacion que dispara el cron externo."""

from fastapi import APIRouter, HTTPException, Request

from dashboard_sync import config, pipeline, reconcile, sheets_client

router = APIRouter()

_sheets_singleton = None
_reconcile_running = False


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
    if not config.DASHBOARD_SYNC_TOKEN or token != config.DASHBOARD_SYNC_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    body = await request.json()
    raw_call = _extract_call_payload(body)
    call_id = raw_call.get("call_id")
    if not call_id:
        raise HTTPException(status_code=422, detail="No se pudo identificar call_id en el payload")

    # Retell dispara varios eventos al mismo webhook (call_started / call_ended /
    # call_analyzed). Si procesamos un call_ended antes de que el post-call
    # analysis esté listo, la fila queda con summary vacío y marcada como
    # sincronizada -> el poll de reconcile la ve presente y la saltea para
    # siempre. Diferimos hasta que el análisis exista; el poll (cada ~10 min) la
    # toma cuando esté completa. Misma comprobación que usa reconcile.
    if not reconcile._analysis_ready(raw_call):
        return {"status": "deferred", "call_id": call_id}

    try:
        await pipeline.process_call(raw_call, _get_sheets_client(), config.BLOB_READ_WRITE_TOKEN)
    except Exception:
        return {"status": "error", "call_id": call_id}

    return {"status": "ok", "call_id": call_id}


@router.post("/webhooks/reconcile")
async def reconcile_endpoint(token: str = ""):
    """Disparado por el scheduler externo (cron-job.org / GitHub Actions) cada
    ~10 min. Poll de Retell -> upsert idempotente en la Sheet. Mismo token
    compartido que callSynced. Devuelve el resumen de la corrida."""
    if not config.DASHBOARD_SYNC_TOKEN or token != config.DASHBOARD_SYNC_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    global _reconcile_running
    if _reconcile_running:
        # Una corrida anterior sigue en curso (el pipeline es idempotente, pero
        # no tiene sentido apilar pasadas). El proximo ping del cron reintenta.
        return {"status": "busy"}

    _reconcile_running = True
    try:
        summary = await reconcile.run(sheets=_get_sheets_client())
    finally:
        _reconcile_running = False

    return {"status": "ok", **summary}
