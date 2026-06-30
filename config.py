""
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
# TTLs y márgenes de cache
# -----------------------------------------------------------------------------
CALL_SESSION_TTL: int = _env_int("CALL_SESSION_TTL", 7200)        # 2 h
JOB_TYPES_TTL: int = _env_int("JOB_TYPES_TTL", 1800)              # 30 min
TOKEN_REFRESH_MARGIN: int = _env_int("TOKEN_REFRESH_MARGIN", 60)  # s antes de exp
