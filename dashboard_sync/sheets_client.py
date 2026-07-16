# dashboard_sync/sheets_client.py
"""Cliente de Google Sheets con upsert idempotente por call_id. Lee/escribe
columnas por nombre de encabezado, nunca por índice fijo, para que reordenar
una columna a mano en la sheet no corrompa datos en silencio."""
import time

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

FIELD_ALIASES = {
    "tools_used": {"tools_used", "tools", "tool_used", "tool_calls"},
}


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


class SheetsClient:
    def __init__(self, worksheet, cache_ttl_s: int = 10):
        self._worksheet = worksheet
        self._cache_ttl_s = cache_ttl_s
        self._headers = None
        self._headers_loaded_at = 0.0
        self._index: dict = {}          # {call_id: numero_de_fila}
        self._row_count = 0
        self._index_loaded_at = 0.0

    def _headers_row(self):
        # Mismo TTL que el indice: si alguien agrega una columna a mano en la
        # sheet, un proceso vivo hace mucho (Render no reinicia solo) tiene
        # que enterarse sin necesitar un redeploy. Sin esto, upsert_call_row
        # sigue escribiendo filas del ancho viejo para siempre y las columnas
        # nuevas quedan en blanco en silencio.
        stale = (time.time() - self._headers_loaded_at) >= self._cache_ttl_s
        if self._headers is None or stale:
            self._headers = self._worksheet.row_values(1)
            self._headers_loaded_at = time.time()
        return self._headers

    @staticmethod
    def _cell_value(value) -> str:
        """Serializa cualquier tipo de campo a texto de celda. Las listas
        (ej. failed_tools) se unen con comas -- sin esto, str(['a','b'])
        escribiría el repr de Python "['a', 'b']" en la celda."""
        if isinstance(value, list):
            return ",".join(str(v) for v in value)
        if value is None:
            return ""
        return str(value)

    def _refresh_index_if_stale(self, force: bool = False):
        if not force and (time.time() - self._index_loaded_at) < self._cache_ttl_s:
            return
        headers = self._headers_row()
        id_col = headers.index("call_id") + 1  # gspread es 1-indexado
        col_values = self._worksheet.col_values(id_col)
        self._index = {v: i + 1 for i, v in enumerate(col_values) if i > 0 and v}
        self._row_count = len(col_values)
        self._index_loaded_at = time.time()

    def upsert_call_row(self, call_id: str, fields: dict) -> None:
        self._refresh_index_if_stale()
        headers = self._headers_row()
        row_fields = dict(fields)
        row_fields["call_id"] = call_id
        row = []
        for header in headers:
            value = row_fields.get(header, "")
            if value == "":
                normalized_header = _normalize_header(header)
                for field, aliases in FIELD_ALIASES.items():
                    if normalized_header in aliases:
                        value = row_fields.get(field, "")
                        break
            row.append(self._cell_value(value))

        if call_id in self._index:
            row_number = self._index[call_id]
            self._worksheet.update(f"A{row_number}", [row])
        else:
            self._worksheet.append_row(row, value_input_option="RAW")
            self._row_count += 1
            self._index[call_id] = self._row_count

    def get_existing_call_ids(self) -> list:
        self._refresh_index_if_stale(force=True)
        return list(self._index.keys())


def connect(sheet_id: str, service_account_info: dict, worksheet_name: str = "Calls", cache_ttl_s: int = 10) -> SheetsClient:
    """Construye un SheetsClient real contra la API de Google. No se cubre con
    unit tests (requiere red + credenciales) — se valida en la verificación
    manual end-to-end del último task de este plan."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(service_account_info, scopes=_SCOPES)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(sheet_id).worksheet(worksheet_name)
    return SheetsClient(worksheet, cache_ttl_s=cache_ttl_s)
