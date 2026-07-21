"""Red de seguridad de booking (backstop).

Si una llamada con intención de reservar juntó datos del cliente pero terminó
SIN un create_job / reschedule exitoso (silencio del agente, error de backend, o
el cliente colgó), avisa a la oficina por email con lo recolectado para que un
humano llame de vuelta. Convierte "silencio total, cero rastro" en "alguien se
entera".

Autocontenido a propósito: NO importa de main.py para evitar el import circular
(main -> dashboard_sync.webhook -> pipeline -> este módulo). Lee las mismas
credenciales de Gmail del entorno (mismo servicio en Render que main.py)."""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
OFFICE_EMAIL = os.getenv("OFFICE_EMAIL", "info@cornerstoneservicesne.com")

BOOKING_INTENTS = {"new_booking", "reschedule"}
SUCCESS_BOOKING_TOOLS = {"create_job", "reschedule_appointment"}

# Campos del session store que sirven para que la oficina devuelva la llamada.
CONTACT_FIELDS = (
    "customerName", "customerPhone", "email", "street", "city", "state", "zip",
    "serviceType", "preferredDate", "preferredTime", "summary",
)
FIELD_LABELS = {
    "customerName": "Name", "customerPhone": "Phone", "email": "Email",
    "street": "Street", "city": "City", "state": "State", "zip": "ZIP",
    "serviceType": "Service", "preferredDate": "Preferred date",
    "preferredTime": "Preferred time", "summary": "Notes",
}


def _tool_events(raw_call):
    inv, results = {}, {}
    for item in raw_call.get("transcript_with_tool_calls") or []:
        role = item.get("role")
        tcid = item.get("tool_call_id")
        if role == "tool_call_invocation":
            inv[tcid] = item
        elif role == "tool_call_result":
            results[tcid] = item
    return inv, results


def _collected_fields(raw_call):
    """Últimos valores guardados por store_call_data durante la llamada."""
    data = {}
    for item in raw_call.get("transcript_with_tool_calls") or []:
        if item.get("role") == "tool_call_invocation" and item.get("name") == "store_call_data":
            try:
                args = json.loads(item.get("arguments") or "{}")
            except (json.JSONDecodeError, TypeError):
                continue
            field, value = args.get("field"), args.get("value")
            if field in CONTACT_FIELDS and value:
                data[field] = value
    return data


def _booking_completed(raw_call):
    """True si algún create_job/reschedule_appointment terminó realmente OK.
    Se mide por el payload (jobId / sin error), no por el flag `successful` de
    Retell, que da true con solo un HTTP 200 aunque el cuerpo sea un error."""
    inv, results = _tool_events(raw_call)
    for tcid, item in inv.items():
        name = item.get("name")
        if name not in SUCCESS_BOOKING_TOOLS:
            continue
        res = results.get(tcid)
        if not res:
            continue
        try:
            content = json.loads(res.get("content") or "{}")
        except (json.JSONDecodeError, TypeError):
            content = {}
        if not isinstance(content, dict) or content.get("error"):
            continue
        if name == "create_job" and content.get("jobId"):
            return True
        if name == "reschedule_appointment":
            return True
    return False


def is_booking_incomplete(raw_call, fields):
    """Devuelve (incompleto: bool, datos_recolectados: dict).
    Incompleto = hubo intención de reservar + se juntaron datos de contacto +
    NO hubo un booking exitoso."""
    intent = (fields or {}).get("intent") or ""
    inv, _ = _tool_events(raw_call)
    tool_names = {i.get("name") for i in inv.values()}
    booking_intent = intent in BOOKING_INTENTS or "check_availability" in tool_names
    if not booking_intent:
        return False, {}

    collected = _collected_fields(raw_call)
    has_contact = bool(
        collected.get("customerName")
        or collected.get("customerPhone")
        or raw_call.get("from_number")
    )
    if not has_contact:
        return False, {}
    if _booking_completed(raw_call):
        return False, {}
    return True, collected


def _rows_html(rows):
    return "".join(
        f"<tr><td style='padding:6px 14px 6px 0;color:#666;white-space:nowrap;vertical-align:top'>{escape(str(l))}</td>"
        f"<td style='padding:6px 0;color:#111'><strong>{escape(str(v))}</strong></td></tr>"
        for l, v in rows
    )


def send_backstop_alert(raw_call, fields):
    """Manda el aviso a la oficina si el booking quedó incompleto.
    Devuelve True si se envió, False si no correspondía o faltan credenciales."""
    incomplete, collected = is_booking_incomplete(raw_call, fields)
    if not incomplete:
        return False
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[backstop] ⚠️ Sin credenciales de Gmail (GMAIL_USER/GMAIL_APP_PASSWORD), no se avisa a la oficina")
        return False

    call_id = raw_call.get("call_id", "")
    name = collected.get("customerName") or "Unknown caller"
    caller_id = raw_call.get("from_number") or ""
    day = (fields or {}).get("day", "")
    start_time = (fields or {}).get("start_time", "")

    rows = [(FIELD_LABELS[f], collected[f]) for f in CONTACT_FIELDS if collected.get(f)]
    if caller_id and not collected.get("customerPhone"):
        rows.insert(1, ("Phone (caller ID)", caller_id))

    subject = f"[Harmony] Booking sin completar — {name} — llamar de vuelta"

    plain = [
        "Una llamada de reserva quedó SIN completar en ServiceTitan.",
        "El cliente dio sus datos pero no se llegó a crear el turno. Llamarlo.",
        "",
        f"Llamada: {day} {start_time}".strip(),
    ]
    plain += [f"{label}: {value}" for label, value in rows]
    if call_id:
        plain += ["", f"Retell call ID: {call_id}"]
    plain += ["", "— Enviado automáticamente por Harmony (red de seguridad de booking)"]
    body = "\n".join(plain)

    html_body = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px;border:1px solid #e0e0e0;border-radius:6px">
      <div style="background:#b45309;color:#fff;padding:10px 16px;border-radius:6px 6px 0 0;font-size:16px">
        Booking sin completar — llamar al cliente</div>
      <div style="padding:16px">
        <p style="color:#444;font-size:14px;margin:0 0 12px">
          El cliente dio sus datos pero la llamada terminó sin crear el turno en ServiceTitan.</p>
        <table style="border-collapse:collapse;font-size:14px">{_rows_html(rows)}</table>
        <p style="color:#aaa;font-size:11px;margin:18px 0 0">
          Enviado automáticamente por Harmony · red de seguridad de booking{f" · Call ID {escape(call_id)}" if call_id else ""}</p>
      </div>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = OFFICE_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"[backstop] ✅ Aviso de booking incompleto enviado a la oficina ({call_id})")
        return True
    except Exception as e:
        print(f"[backstop] ❌ Error enviando aviso: {e}")
        return False
