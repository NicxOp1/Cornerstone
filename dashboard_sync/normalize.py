# dashboard_sync/normalize.py
"""Extrae y normaliza los campos de una llamada de Retell para Sheets.
Autocontenido a propósito: retell_analyzer.py tiene una lógica equivalente
pero está en .gitignore y no se despliega a Render, así que no se puede
importar (ver Global Constraints del plan)."""
from datetime import datetime

import pytz

EASTERN = pytz.timezone("America/New_York")

SPAM_MAX_DURATION_S = 30
SPAM_MAX_USER_WORDS = 5
STALL_SILENCE_THRESHOLD_S = 30


def _ms_to_eastern_day_and_time(ts_ms):
    if not ts_ms:
        return "", ""
    dt_utc = datetime.fromtimestamp(ts_ms / 1000, tz=pytz.UTC)
    dt_eastern = dt_utc.astimezone(EASTERN)
    return dt_eastern.strftime("%Y-%m-%d"), dt_eastern.strftime("%H:%M")


def _count_user_words(call):
    return sum(
        len((item.get("content") or "").split())
        for item in (call.get("transcript_object") or [])
        if item.get("role") == "user"
    )


def _trailing_silence_s(call, duration_s):
    twc = call.get("transcript_with_tool_calls") or []
    last_event_time = 0
    for item in twc:
        role = item.get("role")
        if role in ("agent", "user"):
            words = item.get("words") or []
            if words:
                last_event_time = max(last_event_time, words[-1].get("end", 0))
        elif role in ("tool_call_invocation", "tool_call_result"):
            t = item.get("time_sec")
            if t:
                last_event_time = max(last_event_time, t)
    if not last_event_time:
        return None
    return round(duration_s - last_event_time)


def extract(call: dict) -> dict:
    call_analysis = call.get("call_analysis") or {}
    custom_data = call_analysis.get("custom_analysis_data") or {}
    tool_calls = call.get("tool_calls") or []
    failed_tools = [tc["name"] for tc in tool_calls if tc.get("success") is False and tc.get("name")]

    duration_s = round((call.get("duration_ms") or 0) / 1000)
    day, start_time = _ms_to_eastern_day_and_time(call.get("start_timestamp"))
    user_words = _count_user_words(call)
    silence_s = _trailing_silence_s(call, duration_s)

    call_cost = call.get("call_cost") or {}
    cost_cents = call_cost.get("combined_cost", 0) or 0
    cost_per_min_cents = round(cost_cents / (duration_s / 60), 2) if duration_s else 0

    is_spam = duration_s <= SPAM_MAX_DURATION_S and user_words <= SPAM_MAX_USER_WORDS
    is_stalled = (silence_s or 0) > STALL_SILENCE_THRESHOLD_S or call.get("disconnection_reason") == "inactivity"

    return {
        "call_id": call.get("call_id", ""),
        "day": day,
        "start_time": start_time,
        "duration_s": duration_s,
        "direction": call.get("direction", ""),
        "from_number": call.get("from_number", ""),
        "to_number": call.get("to_number", ""),
        "call_successful": call_analysis.get("call_successful"),
        "sentiment": call_analysis.get("user_sentiment", "Unknown"),
        "intent": custom_data.get("intent", "unknown"),
        "service_type": custom_data.get("service_type", ""),
        "action_completed": custom_data.get("action_completed"),
        "disconnection_reason": call.get("disconnection_reason", ""),
        "cost_cents": cost_cents,
        "cost_per_min_cents": cost_per_min_cents,
        "is_spam": is_spam,
        "is_stalled": is_stalled,
        "failed_tools": failed_tools,
        "summary": call_analysis.get("call_summary", ""),
    }
