# tests/dashboard_sync/test_sheets_client.py
import unittest


class FakeWorksheet:
    """Doble de test de un gspread.Worksheet: fila 1 = headers, resto = datos."""

    def __init__(self, headers, rows=None):
        self._data = [list(headers)] + [list(r) for r in (rows or [])]
        self.col_values_calls = 0

    def row_values(self, row_number):
        return self._data[row_number - 1]

    def col_values(self, col_number):
        self.col_values_calls += 1
        return [
            (row[col_number - 1] if col_number - 1 < len(row) else "")
            for row in self._data
        ]

    def update(self, cell_range, values):
        row_number = int(cell_range[1:])
        self._data[row_number - 1] = list(values[0])

    def append_row(self, values, value_input_option="RAW"):
        self._data.append(list(values))


class UpsertNewCallTests(unittest.TestCase):
    def test_new_call_id_appends_a_row(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "day", "summary"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1", "day": "2026-07-08", "summary": "test"})

        self.assertEqual(len(ws._data), 2)
        self.assertEqual(ws._data[1], ["call_1", "2026-07-08", "test"])

    def test_missing_fields_default_to_empty_string(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "day", "summary"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1"})

        self.assertEqual(ws._data[1], ["call_1", "", ""])

    def test_missing_call_id_field_still_serializes_from_positional_call_id(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "day", "summary"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"day": "2026-07-08", "summary": "test"})

        self.assertEqual(ws._data[1], ["call_1", "2026-07-08", "test"])

    def test_mismatched_call_id_field_uses_positional_call_id(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "day", "summary"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "wrong_id", "day": "2026-07-08", "summary": "test"})

        self.assertEqual(ws._data[1], ["call_1", "2026-07-08", "test"])

    def test_list_fields_are_joined_with_commas_not_python_repr(self):
        """failed_tools llega como lista de normalize.extract() -- tiene que
        quedar en la celda como 'create_job,cancel_appointment', no como el
        repr de Python "['create_job', 'cancel_appointment']"."""
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "failed_tools"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1", "failed_tools": ["create_job", "cancel_appointment"]})

        self.assertEqual(ws._data[1], ["call_1", "create_job,cancel_appointment"])

    def test_tools_used_are_serialized_without_dropping_statuses(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "tools_used"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row(
            "call_1",
            {"tools_used": ["find_customer:ok", "create_job:fail"]},
        )

        self.assertEqual(ws._data[1], ["call_1", "find_customer:ok,create_job:fail"])

    def test_empty_list_field_becomes_empty_string(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "failed_tools"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1", "failed_tools": []})

        self.assertEqual(ws._data[1], ["call_1", ""])


class UpsertExistingCallTests(unittest.TestCase):
    def test_existing_call_id_updates_in_place_without_duplicating(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(
            headers=["call_id", "day", "summary"],
            rows=[["call_1", "2026-07-08", "old summary"]],
        )
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1", "day": "2026-07-08", "summary": "updated summary"})

        self.assertEqual(len(ws._data), 2)
        self.assertEqual(ws._data[1], ["call_1", "2026-07-08", "updated summary"])

    def test_two_writes_in_a_row_for_the_same_call_id_never_duplicate(self):
        """Simula un reintento del mismo evento (Make.com) llegando dos veces."""
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "summary"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1", "summary": "first"})
        client.upsert_call_row("call_1", {"call_id": "call_1", "summary": "retry"})

        self.assertEqual(len(ws._data), 2)
        self.assertEqual(ws._data[1][1], "retry")


class IndexCacheTests(unittest.TestCase):
    def test_index_not_reread_within_ttl_window(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id"], rows=[["call_existing"]])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_2", {"call_id": "call_2"})
        calls_after_first_upsert = ws.col_values_calls

        client.upsert_call_row("call_3", {"call_id": "call_3"})

        self.assertEqual(ws.col_values_calls, calls_after_first_upsert)

    def test_index_rereads_after_ttl_expires(self):
        import time
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id"], rows=[["call_existing"]])
        client = SheetsClient(ws, cache_ttl_s=0.05)

        client.upsert_call_row("call_2", {"call_id": "call_2"})
        calls_after_first_upsert = ws.col_values_calls
        time.sleep(0.06)

        client.upsert_call_row("call_3", {"call_id": "call_3"})

        self.assertGreater(ws.col_values_calls, calls_after_first_upsert)


class HeaderCacheTests(unittest.TestCase):
    def test_headers_not_reread_within_ttl_window(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "summary"])
        client = SheetsClient(ws, cache_ttl_s=10)

        client.upsert_call_row("call_1", {"call_id": "call_1", "summary": "a"})
        ws._data[0] = ["call_id", "summary", "tools_used"]  # alguien agrega una columna a mano
        client.upsert_call_row("call_2", {"call_id": "call_2", "summary": "b", "tools_used": "x"})

        # todavia dentro del TTL: sigue escribiendo con los headers viejos (2 columnas)
        self.assertEqual(ws._data[2], ["call_2", "b"])

    def test_headers_reread_after_ttl_expires(self):
        import time
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id", "summary"])
        client = SheetsClient(ws, cache_ttl_s=0.05)

        client.upsert_call_row("call_1", {"call_id": "call_1", "summary": "a"})
        ws._data[0] = ["call_id", "summary", "tools_used"]
        time.sleep(0.06)
        client.upsert_call_row("call_2", {"call_id": "call_2", "summary": "b", "tools_used": "x"})

        self.assertEqual(ws._data[2], ["call_2", "b", "x"])


class GetExistingCallIdsTests(unittest.TestCase):
    def test_returns_all_call_ids_currently_in_the_sheet(self):
        from dashboard_sync.sheets_client import SheetsClient
        ws = FakeWorksheet(headers=["call_id"], rows=[["call_a"], ["call_b"]])
        client = SheetsClient(ws, cache_ttl_s=10)

        ids = client.get_existing_call_ids()

        self.assertEqual(set(ids), {"call_a", "call_b"})


if __name__ == "__main__":
    unittest.main()
