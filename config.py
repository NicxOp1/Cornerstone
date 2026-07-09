"""
config.py — Configuración centralizada de Cornerstone backend.

Saca a un solo lugar todos los hardcodes que estaban dispersos en main.py
(IDs de negocio, líneas directas, email de oficina, área de servicio, TTLs).
Cada valor se puede sobreescribir por variable de entorno SIN tocar código,
que es lo que pedían las auditorías (docs 02, 04 y 05).

Cómo se usa en main.py:
    import config
    ...
    config.DIRECT_LINES
    config.OFFICE_EMAIL
    config.PLUMBING_JOB_TYPE_IDS
    config.OUTBOUND_JOB_TYPE_ID / config.OUTBOUND_BUSINESS_UNIT_ID
    config.SALEM_PO_BOX / config.SERVICE_RADIUS_MILES
    config.CITIES / config.VALID_STATES / config.MA_STATES
    config.CALL_SESSION_TTL / config.JOB_TYPES_TTL / config.TOKEN_REFRESH_MARGIN
"""

import os
import json


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


def _env_set(name: str, default: set) -> set:
    """Lee un set desde una env var separada por comas (lowercase, sin espacios)."""
    raw = os.getenv(name)
    if not raw:
        return default
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _env_json(name: str, default):
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


# -----------------------------------------------------------------------------
# Líneas directas y contacto de oficina
# -----------------------------------------------------------------------------
# Antes hardcodeado en main.py:48-51 y main.py:46.
# DIRECT_LINES se puede pasar como JSON en la env DIRECT_LINES, ej:
#   DIRECT_LINES={"john":"6033274334","josh":"6033275618"}
DIRECT_LINES: dict = _env_json("DIRECT_LINES", {
    "john": "6033274334",
    "josh": "6033275618",
})

OFFICE_EMAIL: str = os.getenv("OFFICE_EMAIL", "info@cornerstoneservicesne.com")


# -----------------------------------------------------------------------------
# IDs de negocio de ServiceTitan
# -----------------------------------------------------------------------------
# Restricción de licencia: plomería NO disponible en Massachusetts (solo NH).
# Antes hardcodeado en main.py:540.
PLUMBING_JOB_TYPE_IDS: set = {
    int(x) for x in _env_set("PLUMBING_JOB_TYPE_IDS", {"5879699"})
}

# Ruta outbound (campañas). Antes hardcodeado en main.py:1430-1431.
OUTBOUND_JOB_TYPE_ID: int = _env_int("OUTBOUND_JOB_TYPE_ID", 5879699)
OUTBOUND_BUSINESS_UNIT_ID: int = _env_int("OUTBOUND_BUSINESS_UNIT_ID", 5878155)


# -----------------------------------------------------------------------------
# Área de servicio
# -----------------------------------------------------------------------------
# Centro del radio de cobertura (PO Box Salem, MA). Antes en main.py:532.
SALEM_PO_BOX: tuple = (
    float(os.getenv("SALEM_LAT", "42.775")),
    float(os.getenv("SALEM_LON", "-71.217")),
)
SERVICE_RADIUS_MILES: float = float(os.getenv("SERVICE_RADIUS_MILES", "50"))
EARTH_RADIUS_MILES: float = 3958.8

# Lista rápida de ciudades cubiertas (match exacto antes de geocoding).
# Antes en main.py:130-139.
CITIES: set = _env_set("SERVICE_CITIES", {
    "agawam", "amesbury", "attleboro", "barnstable", "beverly", "boston", "braintree",
    "brockton", "cambridge", "chelsea", "chicopee", "easthampton", "everett",
    "fall river", "fitchburg", "framingham", "franklin", "gardner", "gloucester",
    "greenfield", "haverhill", "holyoke", "lawrence", "leominster", "lowell", "lynn",
    "malden", "marlborough", "medford", "melrose", "methuen", "new bedford",
    "newburyport", "newton", "north adams", "northampton", "palmer", "peabody",
    "pittsfield", "quincy", "randolph", "revere", "salem", "somerville", "southbridge",
    "springfield", "taunton", "waltham", "watertown", "west springfield", "westfield",
    "weymouth", "winthrop", "woburn", "worcester", "bridgewater", "amherst", "berlin",
    "claremont", "concord", "dover", "keene", "laconia", "lebanon", "manchester",
    "nashua", "portsmouth", "rochester", "somersworth", "acton", "arlington",
    "atkinson", "derry", "hudson", "windham", "hampton",
})

VALID_STATES: set = _env_set("VALID_STATES", {
    "ma", "nh", "new hampshire", "massachusetts",
})

MA_STATES: set = {"ma", "massachusetts"}

# -----------------------------------------------------------------------------
# Zips por ciudad (inferencia estática — geocode.xyz quedó descartado por
# poco confiable). Clave: "ciudad|st". Solo ciudades donde la lista es corta
# y estable; las ciudades grandes multi-zip (Boston, Worcester, etc.) se
# omiten a propósito → /suggestZip devuelve "unknown" y Harmony pregunta.
# Sobreescribible por env CITY_ZIPS como JSON.
# -----------------------------------------------------------------------------
CITY_ZIPS: dict = _env_json("CITY_ZIPS", {
    # New Hampshire (núcleo del área de servicio)
    "salem|nh": ["03079"],
    "windham|nh": ["03087"],
    "derry|nh": ["03038"],
    "atkinson|nh": ["03811"],
    "hudson|nh": ["03051"],
    "nashua|nh": ["03060", "03062", "03063", "03064"],
    "manchester|nh": ["03101", "03102", "03103", "03104", "03109"],
    "concord|nh": ["03301", "03303"],
    "hampton|nh": ["03842"],
    "portsmouth|nh": ["03801"],
    "dover|nh": ["03820"],
    "rochester|nh": ["03867", "03868"],
    "somersworth|nh": ["03878"],
    "keene|nh": ["03431"],
    "laconia|nh": ["03246"],
    "franklin|nh": ["03235"],
    "claremont|nh": ["03743"],
    "lebanon|nh": ["03766"],
    "berlin|nh": ["03570"],
    # Massachusetts (Merrimack Valley / North Shore, donde llama la mayoría)
    "methuen|ma": ["01844"],
    "lawrence|ma": ["01840", "01841", "01843"],
    "haverhill|ma": ["01830", "01832", "01835"],
    "lowell|ma": ["01850", "01851", "01852", "01854"],
    "amesbury|ma": ["01913"],
    "newburyport|ma": ["01950"],
    "salem|ma": ["01970"],
    "beverly|ma": ["01915"],
    "peabody|ma": ["01960"],
    "gloucester|ma": ["01930"],
    "woburn|ma": ["01801"],
    "melrose|ma": ["02176"],
    "malden|ma": ["02148"],
    "medford|ma": ["02155"],
    "everett|ma": ["02149"],
    "revere|ma": ["02151"],
    "chelsea|ma": ["02150"],
    "winthrop|ma": ["02152"],
    "watertown|ma": ["02472"],
    "waltham|ma": ["02451", "02452", "02453"],
    "randolph|ma": ["02368"],
    "braintree|ma": ["02184"],
    "taunton|ma": ["02780"],
    "brockton|ma": ["02301", "02302"],
    "framingham|ma": ["01701", "01702"],
    "marlborough|ma": ["01752"],
    "franklin|ma": ["02038"],
    "fitchburg|ma": ["01420"],
    "leominster|ma": ["01453"],
    "gardner|ma": ["01440"],
})

# Nombres de estado hablados → abreviatura para la clave de CITY_ZIPS.
STATE_ABBR: dict = {
    "ma": "ma", "massachusetts": "ma",
    "nh": "nh", "new hampshire": "nh",
}


# -----------------------------------------------------------------------------
# TTLs y márgenes de cache
# -----------------------------------------------------------------------------
CALL_SESSION_TTL: int = _env_int("CALL_SESSION_TTL", 7200)        # 2 h
JOB_TYPES_TTL: int = _env_int("JOB_TYPES_TTL", 1800)              # 30 min
TOKEN_REFRESH_MARGIN: int = _env_int("TOKEN_REFRESH_MARGIN", 60)  # s antes de exp

# -----------------------------------------------------------------------------
# Idempotencia de side effects (createJob, sendOfficeMessage, etc.)
# -----------------------------------------------------------------------------
# Evita duplicar una accion real (booking, mail, cancelacion) si Retell reintenta
# el mismo tool call (mismo call_id + mismos args) por un timeout o glitch de red.
IDEMPOTENCY_TTL: int = _env_int("IDEMPOTENCY_TTL_SECONDS", 900)  # 15 min
