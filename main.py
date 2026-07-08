from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import httpx
import asyncio
import hashlib
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import utils as utils
import config
import normalize
import logging
from dotenv import load_dotenv
import os
import json
import pytz
import math
import re
import sys
import requests
from urllib.parse import quote
from html import escape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Load environment variables
load_dotenv()

AUTH_URL_INT = os.getenv("AUTH_URL_INT")
AUTH_URL = os.getenv("AUTH_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
APP_ID = os.getenv("APP_ID")
EASTERN_TIME = pytz.timezone("America/New_York")
MAPS_AUTH = os.getenv("MAPS_AUTH")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
OFFICE_EMAIL = config.OFFICE_EMAIL

DIRECT_LINES = config.DIRECT_LINES

# =============================================================================
# JOB-TYPES CACHE (evita un round-trip a ST en cada checkAvailability)
# =============================================================================

_job_types_cache: dict = {"data": None, "ts": 0.0}
_JOB_TYPES_TTL = config.JOB_TYPES_TTL


async def _get_job_types(headers: dict) -> dict:
    """Devuelve {jobTypeId: [businessUnitId, ...]}. Cachea 30 min."""
    now = time.time()
    if _job_types_cache["data"] and now - _job_types_cache["ts"] < _JOB_TYPES_TTL:
        print("[jobTypes] Cache hit ✅")
        return _job_types_cache["data"]

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/job-types/"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"[jobTypes] ❌ Error {resp.status_code}: {resp.text[:200]}")
        return {}

    mapping = {jt["id"]: jt["businessUnitIds"] for jt in resp.json().get("data", [])}
    _job_types_cache["data"] = mapping
    _job_types_cache["ts"] = now
    print(f"[jobTypes] Fetched and cached {len(mapping)} job types ✅")
    return mapping

# =============================================================================
# CALL SESSION STORE (in-memory, TTL 2 hours)
# =============================================================================

CALL_SESSION_TTL = config.CALL_SESSION_TTL

# { callId: { "_ts": timestamp, "field": "value", ... } }
call_sessions: dict = {}

# Human-readable labels for each field Harmony collects
FIELD_LABELS = {
    "customerName":   "Name",
    "customerPhone":  "Phone number",
    "email":          "Email",
    "street":         "Street address",
    "city":           "City",
    "state":          "State",
    "zip":            "ZIP code",
    "serviceType":    "Service type",
    "preferredDate":  "Appointment date",
    "preferredTime":  "Appointment time",
    "summary":        "Additional notes",
    "customerId":     "Customer ID",
    "locationId":     "Location ID",
    "businessUnitId": "Business unit",
    "jobTypeId":      "Job type",
    "campaignId":     "Campaign",
}

def _cleanup_sessions():
    """Remove sessions older than CALL_SESSION_TTL."""
    now = time.time()
    expired = [k for k, v in call_sessions.items()
               if now - v.get("_ts", 0) > CALL_SESSION_TTL]
    for k in expired:
        del call_sessions[k]

# =============================================================================
# IDEMPOTENCY (evita duplicar side effects si Retell reintenta un tool call)
# =============================================================================

idempotency_cache: dict = {}
idempotency_locks: dict = {}


def _cleanup_idempotency_cache():
    now = time.time()
    expired = [k for k, v in idempotency_cache.items()
               if now - v.get("_ts", 0) > config.IDEMPOTENCY_TTL]
    for k in expired:
        del idempotency_cache[k]
        idempotency_locks.pop(k, None)


def _model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    if hasattr(model, "dict"):
        return model.dict(exclude_none=True)
    return dict(model)


async def _build_idempotency_key(request: Request, operation: str, args_obj) -> "str | None":
    call_id = await _resolve_call_id(request, args_obj)
    if not call_id:
        return None
    payload_json = json.dumps(_model_to_dict(args_obj), sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return f"{operation}:{call_id}:{payload_hash}"


def _should_cache_response(response) -> bool:
    return isinstance(response, dict) and "error" not in response


async def _run_idempotent(request: Request, operation: str, args_obj, action):
    """Envuelve un endpoint de side-effect: si el mismo call_id + mismos args ya
    corrieron dentro del TTL, devuelve la respuesta cacheada en vez de repetir
    la accion real (booking duplicado, mail duplicado, etc.)."""
    _cleanup_idempotency_cache()
    key = await _build_idempotency_key(request, operation, args_obj)
    if not key:
        return await action()

    lock = idempotency_locks.setdefault(key, asyncio.Lock())
    async with lock:
        cached = idempotency_cache.get(key)
        if cached and time.time() - cached.get("_ts", 0) <= config.IDEMPOTENCY_TTL:
            logger.info(f"[idempotency] Reusing cached response for {operation}")
            return cached["response"]
        response = await action()
        if _should_cache_response(response):
            idempotency_cache[key] = {"_ts": time.time(), "response": response}
        return response

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    missing = [e["loc"][-1] for e in errors]
    # No leer request.body() aca: en produccion el ASGI receive() ya se consumio
    # al parsear el body original y volver a awaitearlo cuelga la response (visto
    # en vivo: timeout de 120s en vez de un 400 instantaneo).
    logger.error(f"[ValidationError] Missing/invalid fields: {missing}")
    return JSONResponse(
        status_code=400,
        content={"error": f"Missing or invalid required fields: {missing}"}
    )

# Los endpoints de tools parsean data.args manualmente con .parse_obj() en vez de
# dejar que FastAPI lo valide como parametro de ruta (ver cancelAppointment, etc).
# Sin este handler, un ValidationError ahi adentro es una excepcion sin capturar
# -> 500 crudo en vez de un error legible para Harmony (ej: reasonId invento por
# el LLM en vez de un ID numerico de la tabla).
@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    invalid = [e["loc"][-1] for e in errors]
    logger.error(f"[ValidationError] Invalid tool arguments: {invalid}")
    return JSONResponse(
        status_code=400,
        content={"error": f"Invalid or missing arguments: {invalid}"}
    )

CITIES = config.CITIES

VALID_STATES = config.VALID_STATES

# Auxiliary functions


# Token OAuth de ServiceTitan cacheado en memoria con su expiración.
# Evita pedir un token nuevo en CADA request (latencia extra + riesgo de
# rate-limit en el endpoint de auth). El lock previene race conditions cuando
# varias llamadas concurrentes lo refrescan a la vez.
_token_cache: dict = {"token": None, "exp": 0.0}
_token_lock = asyncio.Lock()


async def get_access_token():
    async with _token_lock:
        # Reusar token vigente (margen de 60s antes de expirar)
        if _token_cache["token"] and time.time() < _token_cache["exp"] - config.TOKEN_REFRESH_MARGIN:
            return _token_cache["token"]
        try:
            print("Fetching access token...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    AUTH_URL,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"grant_type": "client_credentials",
                          "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
                )
            if response.status_code == 200:
                token_data = response.json()
                _token_cache["token"] = token_data.get("access_token")
                _token_cache["exp"] = time.time() + token_data.get("expires_in", 900)
                print("Access token fetched successfully. ✅")
                return _token_cache["token"]
            else:
                # No loguear response.text del endpoint de auth (puede traer detalles sensibles)
                print(f"Error fetching token: status {response.status_code}")
                raise HTTPException(status_code=response.status_code,
                                    detail="Authentication with ServiceTitan failed.")
        except httpx.RequestError as e:
            print(f"Exception while fetching token: {str(e)}")
            raise HTTPException(
                status_code=503, detail="Could not reach ServiceTitan authentication service.")


def _parse_agent_datetime(dt_str: str) -> datetime:
    """Parse agent-provided Eastern wall-clock timestamps with loose ISO input."""
    s = dt_str.strip()
    if s.endswith("Z"):
        s = s[:-1]
    m = re.search(r"[+-]\d{2}:\d{2}$", s)
    if m:
        s = s[:m.start()]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized datetime format: {dt_str!r}")


def massachusetts_to_utc(dt_str: str) -> str:
    """Convierte dígitos Eastern wall-clock a UTC real para ServiceTitan.
    Tolera formatos con/sin segundos y con/sin sufijo Z u offset."""
    dt = _parse_agent_datetime(dt_str)
    dt_eastern = EASTERN_TIME.localize(dt)
    dt_utc = dt_eastern.astimezone(pytz.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_to_eastern(dt_str: str) -> str:
    """Convierte una fecha UTC de ServiceTitan a hora Eastern (Massachusetts).
    Maneja DST automáticamente a través de pytz."""
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    dt_utc = datetime.fromisoformat(dt_str)
    eastern_tz = pytz.timezone("America/New_York")
    dt_eastern = dt_utc.astimezone(eastern_tz)
    return dt_eastern.strftime("%Y-%m-%dT%H:%M:%SZ")


async def get_customer_by_phone(phone):
    print("Getting customer by phone...")
    try:
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?phone={phone}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_customers = await client.get(url_customers, headers=headers)

        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()

            if not customers_data_json.get("data"):
                print("Error: No customers found by phone.")
                return {"error": "Customer not found by phone."}

            customer_data = customers_data_json["data"][0]
            customer = {
                "id": customer_data.get("id"),
                "name": customer_data.get("name")
            }
            print("Customer found by phone ✅")
            return customer

        print(f"Error: Unexpected response {response_customers.status_code} - {response_customers.text}")
        return {"error": f"Unexpected response status: {response_customers.status_code}"}

    except httpx.RequestError as e:
        print(f"Error getting client: {e}")
        return {"error": "Error when making external request."}


async def create_customer(customer: utils.CustomerCreateRequest):
    print("Creating customer ...")

    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        if not customer.name or not customer.number:
            print("Error: Customer name and number are required.")
            return {"error": "Customer name and number are required."}

        # Re-normalizar por si el agente mandó valores dictados por voz.
        customer.number = normalize.normalize_phone(customer.number)
        if customer.email:
            customer.email = normalize.normalize_email(customer.email)

        if customer.locations and isinstance(customer.locations, list) and len(customer.locations) > 0:
            location = customer.locations[0]
        else:
            print("Error: Customer location is missing.")
            return {"error": "Customer location is missing."}

        if hasattr(location, 'address') and location.address:
            location.address.country = location.address.country or "USA"
            location.address.state = location.address.state or "MA"

        payload = {
            "name": customer.name,
            "type": customer.type,
            "address": {
                "street": location.address.street or "",
                "city": location.address.city or "",
                "state": location.address.state or "",
                "zip": location.address.zip or "",
                "country": location.address.country or "",
            },
            "locations": [
                {
                    "name": location.name,
                    "address": {
                        "street": location.address.street or "",
                        "city": location.address.city or "",
                        "zip": location.address.zip or "",
                        "country": location.address.country,
                        "state": location.address.state,
                    },
                }
            ]
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print("Response Status Code:", response.status_code)

            if response.status_code != 200:
                print(f"Error creating customer: {response.text}")
                return {"error": f"Failed to create customer: {response.text}"}

            data = response.json()
            customer_id = data.get("id")
            location_id = data.get("locations", [{}])[0].get("id")

            if not customer_id or not location_id:
                print("Error: Customer or Location ID missing in API response.")
                return {"error": "Customer or Location ID missing in API response."}

            print("Created customer successfully ✅")
            print({"customer_id": customer_id, "location_id": location_id})

            contact_url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers/{customer_id}/contacts"

            if customer.number:
                clean_number = re.sub(r"\D", "", customer.number)
                mobile_payload = {
                    "type": "MobilePhone",
                    "value": clean_number,
                    "memo": "Customer phone number"
                }
                response_mobile = await client.post(contact_url, headers=headers, json=mobile_payload)
                if response_mobile.status_code == 200:
                    print("Mobile contact data added successfully ✅")
                else:
                    print(f"Error adding mobile contact data: {response_mobile.text}")
                    raise HTTPException(
                        status_code=response_mobile.status_code,
                        detail=f"Failed to add mobile contact data: {response_mobile.text}",
                    )

            if customer.email:
                email_payload = {
                    "type": "Email",
                    "value": customer.email,
                    "memo": "Customer email"
                }
                response_email = await client.post(contact_url, headers=headers, json=email_payload)
                if response_email.status_code == 200:
                    print("Email contact data added successfully ✅")
                else:
                    print(f"Error adding email contact data: {response_email.text}")
                    raise HTTPException(
                        status_code=response_email.status_code,
                        detail=f"Failed to add email contact data: {response_email.text}",
                    )

        print("Customer created successfully with contact data added ✅")
        return {"customerId": customer_id, "locationId": location_id}
    except ValueError as e:
        print(f"[create_customer] ValueError: {e}")
        return {"error": "Failed to create customer due to invalid data."}


async def check_availability_time(time, business_units, job_type, access_token=None):
    """
    Devuelve:
      - list[dict]  si encontró slots disponibles
      - []          si la API respondió OK pero no hay turnos (capacidad real vacía)
      - None        si la API de ST no pudo responder (error de red, auth, 5xx, etc.)
    """
    print(f"[check_availability_time] jobType={job_type} BUs={business_units} desde={time}")

    if isinstance(business_units, int):
        business_units = [business_units]
    elif isinstance(business_units, list):
        business_units = [int(bu) for bu in business_units]

    try:
        start_time = _parse_agent_datetime(time)
    except ValueError as exc:
        print(f"[check_availability_time] ❌ Formato de tiempo inválido: {time}")
        raise ValueError("Invalid date/time format. Expected ISO 8601 like YYYY-MM-DDTHH:MM[:SS].") from exc

    if not access_token:
        access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    got_valid_response = False  # True si al menos un intento recibió HTTP 200

    for attempt in range(5):
        current_start = start_time + timedelta(days=attempt * 7)
        current_end = current_start + timedelta(days=13)
        current_end = current_end.replace(hour=23, minute=59, second=0, microsecond=0)

        starts_on_or_after = current_start.replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        ends_on_or_before = current_end.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"[check_availability_time] Intento {attempt + 1}/5 → {starts_on_or_after} a {ends_on_or_before}")

        payload = {
            "startsOnOrAfter": starts_on_or_after,
            "endsOnOrBefore": ends_on_or_before,
            "businessUnitIds": business_units,
            "jobTypeId": job_type,
            "skillBasedAvailability": False
        }

        try:
            # timeout corto: hasta 5 intentos secuenciales. Con 15s c/u podían
            # sumar 75s y colgar la llamada de voz. 8s mantiene el total acotado.
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity",
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                got_valid_response = True
                slots = [
                    {"start": slot["start"], "end": slot["end"]}
                    for slot in response.json().get("availabilities", []) if slot.get("isAvailable")
                ]
                if slots:
                    print(f"[check_availability_time] ✅ {len(slots)} slot(s). Primero: {slots[0]['start']}")
                    return slots
                else:
                    print(f"[check_availability_time] 200 OK pero sin slots en intento {attempt + 1}, reintentando...")
            else:
                print(f"[check_availability_time] ❌ ST respondió {response.status_code}: {response.text[:300]}")

        except httpx.RequestError as e:
            print(f"[check_availability_time] ❌ Error de red: {str(e)}")

    if not got_valid_response:
        print("[check_availability_time] ❌ ST no respondió con 200 en ningún intento (API no disponible).")
        return None  # distinto de [] — señal de falla de API, no de falta de capacidad

    print("[check_availability_time] Sin slots disponibles tras 5 intentos (API OK, capacidad vacía).")
    return []


async def get_technicians_by_businessUnitId(businessUnitId):
    print(f"Getting technicians for Business Unit ID: {businessUnitId}...")

    try:
        url_technicians = f"https://api.servicetitan.io/settings/v2/tenant/{TENANT_ID}/technicians"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response_technicians = await client.get(url_technicians, headers=headers)

        if response_technicians.status_code == 200:
            print("Technicians fetched successfully.")
            response_data = response_technicians.json()
            technicians = [
                tech for tech in response_data.get("data", []) if tech.get("businessUnitId") == businessUnitId
            ]
            if technicians:
                print(f"Found {len(technicians)} technicians for Business Unit ID {businessUnitId}.")
            else:
                print(f"No technicians found for Business Unit ID {businessUnitId}.")
            return technicians
        else:
            print(f"Error fetching technicians. Status Code: {response_technicians.status_code}")
            return {"error": "Failed to retrieve technicians."}

    except httpx.RequestError as e:
        print(f"Error occurred: {str(e)}")
        return {"error": "Checking technicians by business unit failed."}


# Endpoints
@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}


@app.post("/getTime")
async def get_current_boston_time():
    print("Processing getTime request... 🔄")
    eastern = pytz.timezone("America/New_York")
    now_eastern = datetime.now(eastern)

    print(f"Current Boston time: {now_eastern.strftime('%Y-%m-%dT%H:%M:%S')}")
    print("getTime request completed ✅")

    return now_eastern.strftime("%Y-%m-%dT%H:%M:%S")


@app.post("/checkWorkArea")
async def check_work_area(data: utils.AddressCheckToolRequest):
    print("Processing checkWorkArea request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.Address.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    required_text_fields = {
        "street": data.street,
        "city": data.city,
        "state": data.state,
        "zip": data.zip,
    }
    missing_fields = [
        field_name
        for field_name, value in required_text_fields.items()
        if not isinstance(value, str) or not value.strip()
    ]
    if missing_fields:
        return {"error": f"Missing required address fields: {missing_fields}"}

    PO_BOX_SALEM = config.SALEM_PO_BOX
    R = config.EARTH_RADIUS_MILES

    city = data.city.strip().lower()
    state = data.state.strip().lower()

    # Restricción de licencia: plomería solo disponible en NH, no en MA.
    if state in config.MA_STATES and getattr(data, "jobTypeId", None) in config.PLUMBING_JOB_TYPE_IDS:
        print(f"[checkWorkArea] ❌ Plomería no disponible en MA (jobTypeId={data.jobTypeId})")
        return {"error": "Plumbing service is not available in Massachusetts. We can assist you with plumbing in New Hampshire."}

    # Validación rápida: estado permitido y ciudad en lista única
    if state in VALID_STATES and city in CITIES:
        print("Coordinates Checked In List ✅")
        return {"message": "City is in the working area (matched from predefined list)."}

    # Fallback: geocodificación + cálculo de distancia (50 mi desde Salem MA)
    # Política: si geocode falla pero el estado es MA o NH, se permite el booking
    # (el dispatcher verifica en persona). Solo bloqueamos si la dirección queda
    # fuera de los 50 mi y lo podemos confirmar con coordenadas reales.
    # SSRF/inyección: la dirección (input de usuario) NO debe interpolarse cruda
    # en el path. Se URL-encodea y el auth va por params; sin seguir redirects
    # para que nunca se filtre MAPS_AUTH a otro host.
    address = quote(f"{data.street}, {data.city}, {data.state}", safe="")
    url_geocode = f"https://geocode.xyz/{address}"

    _GEOCODE_FAIL_OPEN = {
        "message": "Address is in the working area.",
        "geocode_validation": "pending",
        "validation_note": "Geocode verification was unavailable. Please confirm the service address is within the coverage area before dispatching and add a note to the job summary."
    }

    try:
        resp = await asyncio.to_thread(
            lambda: requests.get(
                url_geocode,
                params={"json": "1", "auth": MAPS_AUTH},
                timeout=8,
                allow_redirects=False,
            )
        )
    except Exception as e:
        print(f"[checkWorkArea] Geocode no disponible: {e}")
        if state in VALID_STATES:
            return _GEOCODE_FAIL_OPEN
        return {"error": "Could not validate the address location. Please try again."}

    if resp.status_code != 200:
        print(f"[checkWorkArea] Geocode respondió {resp.status_code}")
        if state in VALID_STATES:
            return _GEOCODE_FAIL_OPEN
        return {"error": "Failed to fetch geolocation data."}

    try:
        json_data = resp.json()
    except ValueError:
        print("[checkWorkArea] Geocode devolvió un body no-JSON.")
        if state in VALID_STATES:
            return _GEOCODE_FAIL_OPEN
        return {"error": "Could not validate the address location. Please try again."}

    if json_data.get("error") or json_data.get("longt") == "0.00000" or json_data.get("latt") == "0.00000":
        print(f"[checkWorkArea] Geocode no encontró la dirección: {address}")
        if state in VALID_STATES:
            return _GEOCODE_FAIL_OPEN
        return {"error": "The address could not be located. Please verify the address and try again."}

    # ZIP mismatch: solo loggear, NO bloquear. La autoridad es la distancia.
    expected_zip = (json_data.get("standard", {}) or {}).get("postal")
    if expected_zip:
        expected_zip_clean = expected_zip.split('-')[0]
        if expected_zip_clean != data.zip:
            print(f"[checkWorkArea] ZIP mismatch: geocode={expected_zip_clean}, cliente={data.zip} — continuando con check de distancia.")

    try:
        lat = float(json_data.get("latt"))
        lon = float(json_data.get("longt"))
    except (TypeError, ValueError):
        print("[checkWorkArea] No se pudieron parsear las coordenadas de geocode.")
        if state in VALID_STATES:
            return _GEOCODE_FAIL_OPEN
        return {"error": "The provided coordinates are not valid."}

    lat1, lon1 = math.radians(PO_BOX_SALEM[0]), math.radians(PO_BOX_SALEM[1])
    lat2, lon2 = math.radians(lat), math.radians(lon)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = math.sin(delta_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = round(R * c, 2)

    if distance > config.SERVICE_RADIUS_MILES:
        print(f"[checkWorkArea] Fuera del área: {distance} mi desde Salem MA.")
        return {"error": "There are no services available in the area."}

    print(f"[checkWorkArea] ✅ En área: {distance} mi desde Salem MA.")
    return {"message": "Address is in the working area."}


@app.post("/findCustomer")
async def find_customer(data: utils.FindCustomerToolRequest):
    print("Processing findCustomer request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CustomerFindRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    phone = args_obj.number
    if not isinstance(phone, str) or not phone.strip():
        return {"error": "A phone number is required to search for a customer."}
    phone = normalize.normalize_phone(phone)

    try:
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?phone={phone}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_customers = await client.get(url_customers, headers=headers)
        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()
            customers_list = customers_data_json.get("data", [])
            if not customers_list:
                print("No customers found by phone.")
                return {
                    "found": False,
                    "message": "No customers found by phone."
                }
            customers = [
                {"customerId": c.get("id"), "customerName": c.get("name")}
                for c in customers_list
            ]
            print(f"Found {len(customers)} customers by phone ✅")
            return customers
        print(f"Error: Unexpected response {response_customers.status_code} - {response_customers.text}")
        return {"error": f"Unexpected response status: {response_customers.status_code}"}
    except httpx.RequestError as e:
        print(f"Error getting customers: {e}")
        return {"error": "Error when making external request."}


@app.post("/getCustomerLocations")
async def get_customer_locations(data: utils.FindAppointmentToolRequest):

    if isinstance(data.args, dict):
        args_obj = utils.FindAppointmentData.parse_obj(data.args)
    else:
        args_obj = data.args

    customer_id = args_obj.customerId

    print(f"Getting locations for customer ID: {customer_id}... 🔄")

    try:
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        url_location = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/locations?customerId={customer_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_location = await client.get(url_location, headers=headers)

        if response_location.status_code == 200:
            locations_data = response_location.json().get("data", [])
            if not locations_data:
                return {"error": "No locations found for this customer."}

            locations = []
            for loc in locations_data:
                addr = loc.get("address", {})
                formatted_address = f"{addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')}".strip(
                    ", ")
                locations.append({
                    "locationId": loc.get("id"),
                    "locationAddress": formatted_address
                })

            print(f"Locations found: {len(locations)} ✅")
            return {
                "customerId": customer_id,
                "locations": locations
            }
        else:
            print(
                f"Failed to get locations: {response_location.status_code} - {response_location.text}")
            return {"error": "Failed to retrieve locations."}

    except Exception as e:
        print(f"Error fetching locations: {e}")
        return {"error": str(e)}


@app.post("/createLocation")
async def create_location(data: utils.CreateLocationToolRequest, request: Request):
    print("Processing createLocation request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CreateLocationRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    async def action():
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json"
        }

        if data.location.address.zip:
            data.location.address.zip = normalize.normalize_zip(data.location.address.zip)

        payload = {
            "customerId": data.customerId,
            "name": data.location.name,
            "address": data.location.address.model_dump(exclude={"jobTypeId"}, exclude_none=True)
        }

        url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/locations"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Error creating location: {response.text}")
            return {"error": response.text}

        print("createLocation request completed ✅")
        # Suponiendo que response es lo que devuelve el POST al crear la location:
        response_data = response.json()
        location_id = response_data.get("id")

        return {
            "message": "Location created successfully.",
            "locationId": location_id
        }

    return await _run_idempotent(request, "createLocation", args_obj, action)


@app.post("/createCustomer")
async def create_customer_endpoint(data: utils.CreateCustomerToolRequest, request: Request):
    print("Processing createCustomer request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CustomerCreateRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    async def action():
        try:
            response = await create_customer(data)

            if "error" in response:
                print(f"{response['error']}.")
                return {"error": response["error"]}

            print("createCustomer request completed ✅")
            return {
                "customerId": response.get("customerId"),
                "locationId": response.get("locationId"),
                "status": "created"
            }

        except Exception as e:
            print(f"Error processing createCustomer request: {e}")
            return {"error": str(e)}

    return await _run_idempotent(request, "createCustomer", args_obj, action)


@app.post("/checkAvailability")
@app.post("/checkAvailability/")
async def check_availability(data: utils.BookingRequest):
    print("Processing checkAvailability request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.RequestArgs.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    # Obtener mapping jobTypeId → businessUnitIds (cacheado 30 min)
    job_types = await _get_job_types(headers)
    if not job_types:
        return {"error": "Could not retrieve job type information from ServiceTitan. Please try again."}

    business_units = job_types.get(data.jobTypeId)
    if not business_units:
        print(f"[checkAvailability] ❌ jobTypeId {data.jobTypeId} no encontrado en ST.")
        return {"error": f"Job type {data.jobTypeId} not found. Cannot determine business unit."}

    print(f"[checkAvailability] jobTypeId={data.jobTypeId} → BUs={business_units} ✅")

    try:
        available_slots = await check_availability_time(data.time, business_units, data.jobTypeId, access_token)
    except ValueError:
        return {"error": "Invalid date/time format received. Please confirm the requested appointment time."}

    # None = error de API (distinto de lista vacía = genuinamente sin turnos)
    if available_slots is None:
        print("[checkAvailability] ❌ API de ST no disponible.")
        return {"error": "ServiceTitan availability API is currently unavailable. Please try again in a moment."}

    if not available_slots:
        print("[checkAvailability] Sin turnos disponibles.")
        start_date = _parse_agent_datetime(data.time)
        end_date = start_date + timedelta(days=42)
        return {"message": f"No availability found when checking up to {end_date.strftime('%Y-%m-%d')}"}

    print(f"[checkAvailability] ✅ {len(available_slots)} slot(s) encontrados.")
    return {
        "businessUnitId": business_units[0],
        "available_slots": available_slots
    }


@app.post("/createJob")
async def create_job(data: utils.JobCreateToolRequest, request: Request):
    print("Processing createJob request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.JobCreateRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    async def action():
        try:
            if not data.locationId:
                logger.error(f"[createJob] ❌ locationId is missing. customerId={data.customerId}. Agent must call /getCustomerLocations first.")
                return {"error": "locationId is required. Please call getCustomerLocations first to get the correct locationId for this customer."}

            access_token = await get_access_token()
            headers = {
                "Authorization": access_token,
                "ST-App-Key": APP_ID,
                "Content-Type": "application/json",
            }

            # Asegurar formato de fecha con "Z"
            if not data.jobStartTime.endswith("Z"):
                data.jobStartTime += "Z"
            if not data.jobEndTime.endswith("Z"):
                data.jobEndTime += "Z"

            # Trazar conversión de timezone para debugging
            print(f"[createJob] 🕐 Recibido del agente → start: {data.jobStartTime} | end: {data.jobEndTime}")
            # massachusetts_to_utc asume que el agente envía hora Eastern (como la recibió
            # de checkAvailability) y la convierte a UTC real para ServiceTitan.
            try:
                data.jobStartTime = massachusetts_to_utc(data.jobStartTime)
                data.jobEndTime = massachusetts_to_utc(data.jobEndTime)
            except ValueError as e:
                print(f"[createJob] ❌ Formato de fecha/hora inválido: {e}")
                return {"error": "Invalid date/time format received. Please re-confirm the appointment time."}
            print(f"[createJob] 🕐 Enviado a ST (UTC) → start: {data.jobStartTime} | end: {data.jobEndTime}")

            # Construir el payload para ServiceTitan
            payload = {
                "customerId": data.customerId,
                "locationId": data.locationId,
                "businessUnitId": data.businessUnitId,
                "jobTypeId": data.jobTypeId,
                "priority": data.priority,
                "campaignId": data.campaignId,
                "appointments": [
                    {
                        "start": data.jobStartTime,
                        "end": data.jobEndTime,
                        "arrivalWindowStart": data.jobStartTime,
                        "arrivalWindowEnd": data.jobEndTime,
                    }
                ],
                "scheduledDate": datetime.now().strftime("%Y-%m-%d"),
                "scheduledTime": datetime.now().strftime("%H:%M"),
                # escape() evita stored-XSS en la UI de ServiceTitan (el summary se
                # renderiza como HTML para los dispatchers).
                "summary": escape(data.summary or "")
            }

            # Enviar request a ServiceTitan
            url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
            print(f"[createJob] Payload enviado a ServiceTitan: {json.dumps(payload, indent=2)}")

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            print(f"[createJob] Status code: {response.status_code}")
            print(f"[createJob] Response body: {response.text}")

            if response.status_code != 200:
                # Loguear el detalle de ST server-side, pero NO devolverlo al agente.
                print(f"[createJob] ❌ Error creando job: {response.status_code} - {response.text}")
                if response.status_code in (400, 409, 422):
                    return {"error": "That time is no longer available. Let me find another slot for you."}
                return {"error": "Could not create the job right now. Please try again in a moment."}

            job_data = response.json()
            job_id = job_data.get("id")
            appointment_id = job_data.get("lastAppointmentId")

            # No confirmar un agendamiento sin jobId real: el agente tiene PROHIBIDO
            # decir que agendó si no se puede verificar. Sin jobId no se podría
            # cancelar/reprogramar después.
            if not job_id:
                print(f"[createJob] ⚠️ ST respondió 200 pero sin jobId. Body: {response.text[:300]}")
                return {"error": "The booking could not be confirmed. Please try again."}

            print(f"[createJob] ✅ Job creado: jobId={job_id}, appointmentId={appointment_id}")
            return {
                "status": "Job booked",
                "jobId": job_id,
                "appointmentId": appointment_id
            }

        except httpx.RequestError as e:
            print(f"[createJob] ❌ Request error: {str(e)}")
            return {"error": "Unexpected request error"}

    return await _run_idempotent(request, "createJob", args_obj, action)


@app.post("/findAppointments")
async def find_appointments(data: utils.FindAppointmentToolRequest):
    print("Processing findAppointments request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.FindAppointmentData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj
    customer_id = data.customerId

    print(f"Using provided customerId: {customer_id}")

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    def to_eastern(ts: str) -> str:
        if not ts:
            return ""
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(ts)
        return dt_utc.astimezone(EASTERN_TIME).isoformat()

    async def fetch_jobs_by_status(job_status: str):
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
            f"?customerId={customer_id}&jobStatus={job_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        print(f"Error fetching jobs with status {job_status}: {resp.text}")
        return []

    async def fetch_appointments_for_job(job: dict, appointment_status: str):
        job_id = job.get("id")
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments"
            f"?jobId={job_id}&status={appointment_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching appointments for job {job_id}: {resp.text}")
            return []
        appointments = []
        for a in resp.json().get("data", []):
            appointments.append({
                "jobId": job.get("id"),
                "businessUnitId": job.get("businessUnitId"),
                "jobTypeId": job.get("jobTypeId"),
                "summary": job.get("summary", ""),
                "employeeId": job.get("jobGeneratedLeadSource", {}).get("employeeId"),
                "appointmentId": a.get("id"),
                "start": to_eastern(a.get("start")),
                "end": to_eastern(a.get("end")),
            })
        return appointments

    # Fetch los 3 estados en paralelo
    scheduled_jobs, dispatched_jobs, working_jobs = await asyncio.gather(
        fetch_jobs_by_status("Scheduled"),
        fetch_jobs_by_status("Dispatched"),
        fetch_jobs_by_status("InProgress"),
    )
    print(f"Found {len(scheduled_jobs)} Scheduled, {len(dispatched_jobs)} Dispatched, {len(working_jobs)} Working jobs")

    # Fetch appointments en paralelo para todos los jobs
    all_tasks = (
        [(job, "Scheduled") for job in scheduled_jobs] +
        [(job, "Dispatched") for job in dispatched_jobs] +
        [(job, "Working") for job in working_jobs]
    )
    all_results = await asyncio.gather(*[fetch_appointments_for_job(job, status) for job, status in all_tasks])

    scheduled_appointments = []
    dispatched_appointments = []
    working_appointments = []

    idx = 0
    for job in scheduled_jobs:
        scheduled_appointments.extend(all_results[idx]); idx += 1
    for job in dispatched_jobs:
        dispatched_appointments.extend(all_results[idx]); idx += 1
    for job in working_jobs:
        working_appointments.extend(all_results[idx]); idx += 1

    # Si no hay nada encontrado
    if not any([
        scheduled_appointments,
        dispatched_appointments,
        working_appointments,
    ]):
        print("No appointments found.")
        return {"message": "No scheduled, dispatched or working appointments found for this customer."}

    print("findAppointments request completed ✅")
    return {
        "scheduledAppointments": scheduled_appointments,
        "dispatchedAppointments": dispatched_appointments,
        "workingAppointments": working_appointments
    }


@app.post("/findPastAppointments")
async def find_past_appointments(data: utils.FindAppointmentToolRequest):
    print("Processing findPastAppointments request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.FindAppointmentData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj
    customer_id = data.customerId

    print(f"Using provided customerId: {customer_id}")

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    def to_eastern_past(ts: str) -> str:
        if not ts:
            return ""
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(ts)
        return dt_utc.astimezone(EASTERN_TIME).isoformat()

    async def fetch_jobs_by_status_past(job_status: str):
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
            f"?customerId={customer_id}&jobStatus={job_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        print(f"Error fetching jobs with status {job_status}: {resp.text}")
        return []

    async def fetch_appointments_for_job_past(job: dict, appointment_status: str):
        job_id = job.get("id")
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments"
            f"?jobId={job_id}&status={appointment_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching appointments for job {job_id}: {resp.text}")
            return []
        appointments = []
        for a in resp.json().get("data", []):
            appointments.append({
                "jobId": job.get("id"),
                "businessUnitId": job.get("businessUnitId"),
                "jobTypeId": job.get("jobTypeId"),
                "summary": job.get("summary", ""),
                "employeeId": job.get("jobGeneratedLeadSource", {}).get("employeeId"),
                "appointmentId": a.get("id"),
                "start": to_eastern_past(a.get("start")),
                "end": to_eastern_past(a.get("end")),
            })
        return appointments

    hold_jobs, done_jobs, canceled_jobs = await asyncio.gather(
        fetch_jobs_by_status_past("Hold"),
        fetch_jobs_by_status_past("Completed"),
        fetch_jobs_by_status_past("Canceled"),
    )
    print(f"Found {len(hold_jobs)} Hold, {len(done_jobs)} Done, {len(canceled_jobs)} Canceled jobs")

    all_past_tasks = (
        [(job, "Hold") for job in hold_jobs] +
        [(job, "Done") for job in done_jobs] +
        [(job, "Canceled") for job in canceled_jobs]
    )
    all_past_results = await asyncio.gather(*[fetch_appointments_for_job_past(job, status) for job, status in all_past_tasks])

    hold_appointments = []
    done_appointments = []
    canceled_appointments = []

    idx = 0
    for job in hold_jobs:
        hold_appointments.extend(all_past_results[idx]); idx += 1
    for job in done_jobs:
        done_appointments.extend(all_past_results[idx]); idx += 1
    for job in canceled_jobs:
        canceled_appointments.extend(all_past_results[idx]); idx += 1

    if not any([hold_appointments, done_appointments, canceled_appointments]):
        print("No past appointments found.")
        return {"message": "No past appointments found for this customer."}

    print("findPastAppointments request completed ✅")
    return {
        "holdAppointments": hold_appointments,
        "doneAppointments": done_appointments,
        "canceledAppointments": canceled_appointments,
    }


@app.post("/rescheduleAppointmentTimeAvailability")
async def reschedule_appointment_time_availability(data: utils.ReScheduleToolRequest):
    print("Processing rescheduleAppointmentTimeAvailability request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.ReScheduleData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    job_type_id = data.jobTypeId
    business_unit_id = data.businessUnitId
    desired_time = data.newSchedule

    if not job_type_id or not business_unit_id:
        print("Missing jobTypeId or businessUnitId in request.")
        return {"error": "Missing jobTypeId or businessUnitId in request."}

    print(
        f"Checking availability for businessUnitId={business_unit_id}, jobTypeId={job_type_id}, around {desired_time}...")
    try:
        slots_available = await check_availability_time(desired_time, business_unit_id, job_type_id)
    except ValueError:
        return {"error": "Invalid date/time format received. Please confirm the requested appointment time."}

    if slots_available is None:
        print("[rescheduleAvailability] ❌ API de ST no disponible.")
        return {"error": "ServiceTitan availability API is currently unavailable. Please try again."}

    if slots_available:
        # ST capacity API devuelve horarios en Eastern wall-clock mislabeled como "Z".
        # No convertir: el agente debe recibirlos igual que en /checkAvailability.
        # La conversión a UTC real ocurre en /rescheduleAppointment via massachusetts_to_utc.
        print(f"[rescheduleAvailability] ✅ {len(slots_available)} slot(s) encontrados.")
        return {"availableSlots": slots_available}

    print("[rescheduleAvailability] Sin turnos disponibles.")
    start_date = _parse_agent_datetime(data.newSchedule)
    end_date = start_date + timedelta(days=42)
    return {"message": f"No availability found when checking up to {end_date.strftime('%Y-%m-%d')}"}


@app.post("/rescheduleAppointment")
async def reschedule_appointment(data: utils.ReScheduleToolRequest, request: Request):
    print("Processing rescheduleAppointment request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.ReScheduleData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    async def action():
        access_token = await get_access_token()

        appointment_id = data.appointmentId
        technician_id = data.employeeId
        new_schedule = data.newSchedule

        if not appointment_id:
            return {"error": "Missing appointmentId in request."}
        if not isinstance(new_schedule, str) or not new_schedule.strip():
            return {"error": "Missing newSchedule in request."}

        # 1. Unassign technician if provided
        st_headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        if technician_id:
            tech_ids = technician_id if isinstance(technician_id, list) else [technician_id]
            print(f"Unassigning technician(s) {tech_ids} from appointment {appointment_id}...")
            url_unassign = (
                f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}"
                "/appointment-assignments/unassign-technicians"
            )
            unassign_payload = {
                "jobAppointmentId": appointment_id,
                "technicianIds": tech_ids
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp_unassign = await client.patch(url_unassign, json=unassign_payload, headers=st_headers)
            if resp_unassign.status_code == 200:
                print("Technician unassigned successfully ✅")
            else:
                print(f"Failed to unassign technician: {resp_unassign.text}")

        # 2. Ensure the new_schedule string ends with "Z"
        if not new_schedule.endswith("Z"):
            new_schedule += "Z"

        # 3. Convert from Massachusetts local time to UTC
        try:
            start_utc = massachusetts_to_utc(new_schedule)
        except ValueError:
            return {"error": "Invalid date/time format received. Please confirm the requested appointment time."}

        # 4. Calculate end_utc = start_utc + 3 hours
        start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
        end_dt = start_dt + timedelta(hours=3)
        end_utc = end_dt.isoformat().replace("+00:00", "Z")

        # 5. Send the reschedule PATCH
        print(f"Rescheduling appointment {appointment_id} to start {start_utc} and end {end_utc}...")
        url_resch = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}"
            f"/appointments/{appointment_id}/reschedule"
        )
        resch_payload = {
            "start": start_utc,
            "end": end_utc,
            "arrivalWindowStart": start_utc,
            "arrivalWindowEnd": end_utc
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.patch(url_resch, json=resch_payload, headers=st_headers)

        if resp.status_code == 200:
            print("rescheduleAppointment request completed ✅")
            return {"status": "rescheduleAppointment request processed successfully"}
        else:
            print(f"Failed to reschedule appointment: {resp.text}")
            return {
                "error": f"Request error: {resp.status_code}",
                "details": resp.text
            }

    return await _run_idempotent(request, "rescheduleAppointment", args_obj, action)


@app.post("/cancelAppointment")
async def cancel_appointment(data: utils.CancelJobAppointmentToolRequest, request: Request):
    print("Processing cancelAppointment request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CancelJobAppointment.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    async def action():
        # extraer directamente los datos necesarios
        job_id = data.jobId
        reason_id = data.reasonId
        memo = data.memo

        if not job_id:
            print("Missing jobId in request.")
            return {"error": "Missing jobId in request."}

        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        # llamar al endpoint de cancelación
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}/cancel"
        payload = {
            "reasonId": reason_id,
            "memo": memo
        }

        print(f"Cancelling job {job_id} with reason {reason_id}...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.put(url, headers=headers, json=payload)
        print(f"External API responded: {resp.status_code}")

        if resp.status_code == 200:
            # a veces el body viene vacío
            if not resp.text.strip():
                print("cancelAppointment request completed ✅")
                return {"message": "Job canceled successfully"}
            print("cancelAppointment request completed ✅")
            return resp.json()
        elif resp.status_code == 404:
            print("Job ID not found.")
            return {"error": "Job ID not found", "details": resp.json()}
        else:
            try:
                st_detail = resp.json()
            except Exception:
                st_detail = resp.text.strip()
            print(f"Failed to cancel job: {st_detail}")
            return {
                "error": f"Request error: {resp.status_code}",
                "details": st_detail or "ServiceTitan rejected the cancellation request."
            }

    return await _run_idempotent(request, "cancelAppointment", args_obj, action)


@app.post("/updateJobSummary")
async def update_job_summary(data: utils.UpdateJobSummaryToolRequest, request: Request):
    print("Processing updateJobSummary request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.UpdateJobSummary.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    async def action():
        job_id = data.jobId
        info = data.info

        if not job_id or not info:
            return {"error": "Missing required fields: jobId and info"}

        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        print(f"Fetching current summary for job ID {job_id}...")

        job_url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            job_resp = await client.get(job_url, headers=headers)

        if job_resp.status_code != 200:
            return {
                "error": f"Failed to fetch job data for job ID {job_id}",
                "status_code": job_resp.status_code,
                "details": job_resp.text
            }

        job_data = job_resp.json()
        current_summary = job_data.get("summary", "")

        new_summary = f"<p>{escape(info or '')}</p>"
        updated_summary = f"{current_summary}\n\n{new_summary}".strip() if current_summary else new_summary

        print(f"Updating summary for job ID {job_id}...")
        patch_url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}"
        patch_payload = {"summary": updated_summary}

        async with httpx.AsyncClient(timeout=15.0) as client:
            patch_resp = await client.patch(patch_url, headers=headers, json=patch_payload)

        if patch_resp.status_code == 200:
            print("updateJobSummary completed ✅")
            return {"status": "Job summary updated"}
        else:
            print(f"Failed to update job summary: {patch_resp.text}")
            return {
                "error": "Failed to update job summary.",
                "status_code": patch_resp.status_code,
                "details": patch_resp.text
            }

    return await _run_idempotent(request, "updateJobSummary", args_obj, action)


# Outbound

@app.post("/checkAvailabilityOutbound")
@app.post("/checkAvailabilityOutbound/")
async def check_availability_outbound(data: utils.BookingRequestOutbound):
    print("Processing checkAvailabilityOutbound request... 🔄")
    jobType = config.OUTBOUND_JOB_TYPE_ID
    business_unit = config.OUTBOUND_BUSINESS_UNIT_ID

    if isinstance(data.args, dict):
        args_obj = utils.RequestArgsOutbound.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    print("[checkAvailabilityOutbound] Checking availability...")

    try:
        available_slots = await check_availability_time(data.time, business_unit, jobType)
    except ValueError:
        return {"error": "Invalid date/time format received. Please confirm the requested appointment time."}

    if available_slots is None:
        print("[checkAvailabilityOutbound] ❌ API de ST no disponible.")
        return {"error": "ServiceTitan availability API is currently unavailable. Please try again."}

    if not available_slots:
        print("[checkAvailabilityOutbound] Sin turnos disponibles.")
        return {"message": "No availability found."}

    print(f"[checkAvailabilityOutbound] ✅ {len(available_slots)} slot(s).")
    return {"available_slots": available_slots}


async def _resolve_call_id(request: Request, args_obj):
    """Get the Retell call_id from the request body's 'call' object,
    falling back to whatever the agent passed in args."""
    try:
        body = await request.json()
        call_obj = body.get("call") or {}
        cid = call_obj.get("call_id") or body.get("call_id")
        if cid:
            return cid
    except Exception:
        pass
    return getattr(args_obj, "callId", None)


@app.post("/storeCallData")
async def store_call_data(data: utils.StoreCallDataToolRequest, request: Request):
    print("Processing storeCallData request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.StoreCallDataRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    _cleanup_sessions()

    call_id = await _resolve_call_id(request, args_obj)
    if not call_id:
        print("[storeCallData] ❌ Could not determine call ID.")
        return {"error": "Could not determine the call ID for this session."}

    if call_id not in call_sessions:
        call_sessions[call_id] = {"_ts": time.time()}

    # El agente puede mandar el valor dictado ("six oh three...", "j o e at...").
    # Se normaliza acá para que ST y el mail a la oficina reciban el valor final.
    clean_value = normalize.normalize_call_field(args_obj.field, args_obj.value)

    # Dedupe: mismo campo + mismo valor ya guardado → no-op (bug conocido:
    # burst de 8 stores idénticos en el mismo ms tras un transfer fallido).
    if call_sessions[call_id].get(args_obj.field) == clean_value:
        print(f"[storeCallData] callId={call_id} | {args_obj.field} sin cambios (dedupe) ✅")
        return {"status": "stored", "field": args_obj.field, "value": clean_value}

    call_sessions[call_id][args_obj.field] = clean_value
    call_sessions[call_id]["_ts"] = time.time()

    if clean_value != args_obj.value:
        print(f"[storeCallData] callId={call_id} | {args_obj.field} normalizado: '{args_obj.value}' → '{clean_value}'")
    print(f"[storeCallData] callId={call_id} | {args_obj.field} = {clean_value} ✅")
    return {"status": "stored", "field": args_obj.field, "value": clean_value}


@app.post("/getCallData")
async def get_call_data(data: utils.GetCallDataToolRequest, request: Request):
    print("Processing getCallData request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.GetCallDataRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    call_id = await _resolve_call_id(request, args_obj)
    session = call_sessions.get(call_id, {})

    # Build ordered field list (skip internal keys starting with _)
    fields = []
    for field, label in FIELD_LABELS.items():
        value = session.get(field)
        if value:
            fields.append({"field": field, "label": label, "value": value})

    if not fields:
        print(f"[getCallData] callId={call_id} — no data found")
        return {"fields": [], "readableScript": "I don't have any stored information for this call yet."}

    # Build readable script Harmony reads aloud
    readable = ". ".join([f"{f['label']}: {f['value']}" for f in fields])

    print(f"[getCallData] callId={call_id} — {len(fields)} fields ✅")
    return {"fields": fields, "readableScript": readable}


@app.post("/updateCallField")
async def update_call_field(data: utils.UpdateCallFieldToolRequest, request: Request):
    print("Processing updateCallField request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.UpdateCallFieldRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    call_id = await _resolve_call_id(request, args_obj)
    if not call_id:
        print("[updateCallField] ❌ Could not determine call ID.")
        return {"error": "Could not determine the call ID for this session."}

    if call_id not in call_sessions:
        print(f"[updateCallField] callId={call_id} not found, creating new session")
        call_sessions[call_id] = {"_ts": time.time()}

    old_value = call_sessions[call_id].get(args_obj.field, "—")
    clean_value = normalize.normalize_call_field(args_obj.field, args_obj.value)
    call_sessions[call_id][args_obj.field] = clean_value
    call_sessions[call_id]["_ts"] = time.time()

    print(f"[updateCallField] callId={call_id} | {args_obj.field}: '{old_value}' → '{clean_value}' ✅")
    return {"status": "updated", "field": args_obj.field, "oldValue": old_value, "newValue": clean_value}


@app.post("/clearCallData")
async def clear_call_data(data: utils.ClearCallDataToolRequest, request: Request):
    print("Processing clearCallData request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.ClearCallDataRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    call_id = await _resolve_call_id(request, args_obj)
    if call_id and call_id in call_sessions:
        del call_sessions[call_id]
        print(f"[clearCallData] callId={call_id} cleared ✅")
        return {"status": "cleared"}

    print(f"[clearCallData] callId={call_id} not found (already cleared or expired)")
    return {"status": "not_found"}


@app.post("/getDirectLine")
async def get_direct_line(data: utils.DirectLineToolRequest):
    print("Processing getDirectLine request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.DirectLineRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    name = args_obj.name.strip().lower()

    for key, phone in DIRECT_LINES.items():
        if key in name:
            print(f"Direct line found for '{key}' ✅")
            return {"name": key.capitalize(), "phone": phone}

    print(f"No direct line found for '{name}'")
    return {"message": "We don't have contact information for that person. Is there anything else I can help you with?"}


@app.post("/suggestZip")
async def suggest_zip(data: utils.SuggestZipToolRequest):
    """Inferencia de zip por tabla estática (geocode.xyz descartado por poco
    confiable). single → Harmony lo usa sin preguntar; multiple → Harmony
    pregunta '¿es XXXXX o YYYYY?'; unknown → Harmony pide el zip como siempre."""
    print("Processing suggestZip request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.SuggestZipRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    city = (args_obj.city or "").strip().lower()
    state_raw = (args_obj.state or "").strip().lower()
    state = config.STATE_ABBR.get(state_raw, state_raw[:2])

    if not city or not state:
        return {"status": "unknown", "message": "Ask the caller for their zip code."}

    zips = config.CITY_ZIPS.get(f"{city}|{state}")
    if not zips:
        print(f"[suggestZip] Sin datos para {city}|{state} → unknown")
        return {"status": "unknown", "message": "No zip data for this city. Ask the caller for their zip code."}

    if len(zips) == 1:
        print(f"[suggestZip] ✅ {city}|{state} → {zips[0]} (único)")
        return {"status": "single", "zip": zips[0],
                "message": "Use this zip code silently. Do not ask the caller for it — just include it in the final read-back."}

    print(f"[suggestZip] {city}|{state} → {len(zips)} opciones")
    return {"status": "multiple", "zips": zips,
            "message": "Ask the caller which of these zip codes is theirs, e.g. 'And is that the 03060 or 03062 zip?'"}


def _send_gmail(subject: str, body: str, html_body: str = None):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("❌ Gmail credentials not configured (GMAIL_USER / GMAIL_APP_PASSWORD missing)")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = OFFICE_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


@app.post("/sendOfficeMessage")
async def send_office_message(data: utils.OfficeMessageToolRequest, request: Request):
    print("Processing sendOfficeMessage request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.OfficeMessageRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    async def action():
        # Merge both naming conventions (callerName/callerPhone and name/number)
        name = args_obj.name or args_obj.callerName
        phone = normalize.normalize_phone(args_obj.number or args_obj.callerPhone)
        email = normalize.normalize_email(args_obj.email) if args_obj.email else None
        is_emergency = str(args_obj.isEmergency).strip().lower() in ("true", "yes", "1")

        if not any([args_obj.question, name, phone, args_obj.reason, args_obj.callback]):
            print("sendOfficeMessage: no usable content provided ❌")
            return {"error": "No message content provided."}

        # Enriquecer con todo lo recolectado durante la llamada (session store):
        # dirección, servicio, fecha/hora pedida — datos que antes no llegaban.
        call_id = await _resolve_call_id(request, args_obj)
        session = call_sessions.get(call_id, {}) if call_id else {}

        caller_rows = [
            ("Name", name),
            ("Phone", phone),
            ("Email", email or session.get("email")),
            ("Reason", args_obj.reason),
            ("Preferred callback", args_obj.callback),
        ]
        caller_rows = [(label, value) for label, value in caller_rows if value]

        call_rows = []
        for field, label in FIELD_LABELS.items():
            value = session.get(field)
            if value and field not in ("customerName", "customerPhone", "email"):
                call_rows.append((label, value))

        now_eastern = datetime.now(EASTERN_TIME).strftime("%A, %B %d — %I:%M %p ET")

        # Subject: tipo + nombre, para que la bandeja de la oficina se lea sola.
        who = name or "Unknown caller"
        if is_emergency:
            subject = f"🚨 [Harmony] EMERGENCY — {who} needs immediate callback"
        elif args_obj.question:
            subject = f"[Harmony] Question from {who} — needs an answer"
        else:
            subject = f"[Harmony] Callback request — {who}"

        # --- Cuerpo texto plano (fallback) ---
        plain_lines = [f"{'EMERGENCY — call back ASAP' if is_emergency else 'Follow-up needed'}",
                       f"Received: {now_eastern}", ""]
        plain_lines += [f"{label}: {value}" for label, value in caller_rows]
        if args_obj.question:
            plain_lines += ["", f"Question / message: {args_obj.question}"]
        if call_rows:
            plain_lines += ["", "Details collected during the call:"]
            plain_lines += [f"  {label}: {value}" for label, value in call_rows]
        if call_id:
            plain_lines += ["", f"Retell call ID: {call_id}"]
        plain_lines += ["", "— Sent automatically by Harmony (Cornerstone voice agent)"]
        body = "\n".join(plain_lines)

        # --- Cuerpo HTML ---
        def _rows_html(rows):
            return "".join(
                f"<tr><td style='padding:6px 14px 6px 0;color:#666;white-space:nowrap;vertical-align:top'>{escape(str(l))}</td>"
                f"<td style='padding:6px 0;color:#111'><strong>{escape(str(v))}</strong></td></tr>"
                for l, v in rows
            )

        banner = (
            "<div style='background:#c0392b;color:#fff;padding:10px 16px;border-radius:6px 6px 0 0;font-size:16px'>"
            "🚨 EMERGENCY — call back ASAP</div>"
            if is_emergency else
            "<div style='background:#2c3e50;color:#fff;padding:10px 16px;border-radius:6px 6px 0 0;font-size:16px'>"
            "Message from Harmony</div>"
        )
        question_html = (
            f"<p style='background:#f6f6f6;border-left:4px solid #2c3e50;padding:10px 14px;margin:14px 0'>"
            f"{escape(args_obj.question)}</p>" if args_obj.question else ""
        )
        call_details_html = (
            f"<h3 style='margin:18px 0 4px;font-size:14px;color:#444'>Details collected during the call</h3>"
            f"<table style='border-collapse:collapse;font-size:14px'>{_rows_html(call_rows)}</table>"
            if call_rows else ""
        )
        html_body = f"""
        <div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px;border:1px solid #e0e0e0;border-radius:6px">
          {banner}
          <div style="padding:16px">
            <p style="color:#888;font-size:12px;margin:0 0 12px">Received {escape(now_eastern)}</p>
            <table style="border-collapse:collapse;font-size:14px">{_rows_html(caller_rows)}</table>
            {question_html}
            {call_details_html}
            <p style="color:#aaa;font-size:11px;margin:18px 0 0">
              Sent automatically by Harmony — Cornerstone voice agent{f" · Call ID {escape(call_id)}" if call_id else ""}
            </p>
          </div>
        </div>
        """

        success = await asyncio.to_thread(_send_gmail, subject, body, html_body)

        if success:
            print("sendOfficeMessage completed ✅")
            return {"status": "Message sent to office successfully"}
        else:
            print("sendOfficeMessage failed ❌")
            return {"error": "Failed to send message. Please try again or call the office directly."}

    return await _run_idempotent(request, "sendOfficeMessage", args_obj, action)


# start the server: fastapi dev main.py

