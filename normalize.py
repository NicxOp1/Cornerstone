"""
normalize.py — Normalización server-side de datos dictados por voz.

Harmony (Retell + gpt-4.1) a veces guarda los valores tal como el caller los
dictó: "six oh three five five five..." o "j o a c o at gmail dot com".
ServiceTitan y el mail a la oficina necesitan el valor final limpio.

La defensa es doble: el prompt le ordena al agente guardar el formato final,
y este módulo re-normaliza en el backend por si el LLM igual manda dictado.

Regla de oro: si el valor ya viene limpio, estas funciones son no-op.
Nunca deben romper un valor que ya estaba bien (producción depende de eso).
"""

import re

# Palabras que representan dígitos al dictar números (contexto teléfono/zip).
_DIGIT_WORDS = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "won": "1",
    "two": "2", "to": "2", "too": "2",
    "three": "3",
    "four": "4", "for": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8", "ate": "8",
    "nine": "9",
}

_MULTIPLIERS = {"double": 2, "triple": 3}

# Tokens hablados que corresponden a símbolos de email.
_EMAIL_SYMBOLS = {
    "at": "@",
    "dot": ".", "period": ".", "point": ".",
    "underscore": "_",
    "dash": "-", "hyphen": "-", "minus": "-",
    "plus": "+",
}

# En emails NO mapeamos "o"→0 ni "to"/"for"→dígito: son letras/palabras válidas.
_EMAIL_DIGIT_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}


def _spoken_to_digits(text: str) -> str:
    """'six oh three, double five' → '60355'. Ignora tokens que no son dígitos."""
    tokens = re.split(r"[\s,\-\.]+", text.lower())
    out = []
    repeat = 1
    for tok in tokens:
        if not tok:
            continue
        if tok in _MULTIPLIERS:
            repeat = _MULTIPLIERS[tok]
            continue
        if tok in _DIGIT_WORDS:
            out.append(_DIGIT_WORDS[tok] * repeat)
        elif tok.isdigit():
            out.append(tok * repeat if repeat > 1 and len(tok) == 1 else tok)
        # cualquier otro token ("my", "number", "is") se ignora
        repeat = 1
    return "".join(out)


def normalize_phone(raw) -> str:
    """Devuelve el número en dígitos. No-op para valores ya limpios.

    - "+16035551234" / "(603) 555-1234" → se quita solo el formato.
    - "six oh three five five five one two three four" → "6035551234".
    """
    if not isinstance(raw, str) or not raw.strip():
        return raw
    s = raw.strip()
    stripped = re.sub(r"[()\s\-\.]", "", s)
    # Ya es un número (con o sin +): devolver sin tocar el contenido.
    if re.fullmatch(r"\+?\d+", stripped):
        return stripped
    digits = _spoken_to_digits(s)
    return digits if digits else s


def normalize_email(raw) -> str:
    """Devuelve el email en formato estándar lowercase. No-op si ya está limpio.

    "j o a c o at gmail dot com" → "joaco@gmail.com"
    "Joaco@Gmail.com"            → "joaco@gmail.com"
    """
    if not isinstance(raw, str) or not raw.strip():
        return raw
    s = raw.strip()
    if " " not in s and "@" in s:
        return s.lower()

    tokens = re.split(r"\s+", s.lower())
    parts = []
    for tok in tokens:
        tok = tok.strip(",;:")
        if not tok:
            continue
        if tok in _EMAIL_SYMBOLS:
            parts.append(_EMAIL_SYMBOLS[tok])
        elif tok in _EMAIL_DIGIT_WORDS:
            parts.append(_EMAIL_DIGIT_WORDS[tok])
        else:
            parts.append(tok)
    candidate = "".join(parts)
    # Solo aceptar el rearmado si parece un email real; si no, devolver original.
    if re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", candidate):
        return candidate
    return s


def normalize_zip(raw) -> str:
    """Devuelve el zip como 5 dígitos. No-op si no se puede interpretar.

    "oh three oh seven nine" → "03079"; "01835-1234" → "01835".
    """
    if not isinstance(raw, str) or not raw.strip():
        return raw
    s = raw.strip()
    digits = re.sub(r"\D", "", s)
    if not digits:
        digits = _spoken_to_digits(s)
    if len(digits) >= 5:
        return digits[:5]
    return digits if digits else s


def has_full_name(raw) -> bool:
    """True si el valor tiene al menos dos palabras (nombre + apellido).

    No valida contenido, solo forma: "John" -> False, "John Smith" -> True.
    """
    if not isinstance(raw, str):
        return False
    return len(raw.strip().split()) >= 2


def normalize_call_field(field: str, value):
    """Normalización por campo para el call-session store."""
    if not isinstance(value, str):
        return value
    if field == "customerPhone":
        return normalize_phone(value)
    if field == "email":
        return normalize_email(value)
    if field == "zip":
        return normalize_zip(value)
    return value.strip()
