# tests/dashboard_sync/test_callback_sheet.py
import unittest
from unittest.mock import patch


class FakeWorksheet:
    """Mismo doble de test que usa test_sheets_client.py."""

    def __init__(self, headers, rows=None):
        self._data = [list(headers)] + [list(r) for r in (rows or [])]

    def row_values(self, row_number):
        return self._data[row_number - 1]

    def col_values(self, col_number):
        return [
            (row[col_number - 1] if col_number - 1 < len(row) else "")
            for row in self._data
        ]

    def update(self, cell_range, values):
        row_number = int(cell_range[1:])
        self._data[row_number - 1] = list(values[0])

    def append_row(self, values, value_input_option="RAW"):
        self._data.append(list(values))


HEADERS = [
    "Timestamp", "Status", "Full Name", "Phone Number",
    "Reason for Call", "Preferred Callback Time", "Email (optional)", "Call Id",
]


class AppendCallbackTests(unittest.TestCase):
    def test_emergency_goes_to_emergency_tab(self):
        from dashboard_sync import callback_sheet
        callback_sheet._worksheet_cache.clear()
        ws = FakeWorksheet(headers=HEADERS)

        with patch.object(callback_sheet, "_get_worksheet", return_value=ws) as mock_get:
            callback_sheet.append_callback(
                name="Joan Day", number="19126595571", reason="heat pump leaking",
                callback="Morning", is_emergency=True, email=None, call_id="call_1",
            )
            mock_get.assert_called_once_with("Emergency")

        self.assertEqual(len(ws._data), 2)
        row = dict(zip(HEADERS, ws._data[1]))
        self.assertEqual(row["Full Name"], "Joan Day")
        self.assertEqual(row["Phone Number"], "19126595571")
        self.assertEqual(row["Call Id"], "call_1")

    def test_non_emergency_goes_to_non_emergency_tab(self):
        from dashboard_sync import callback_sheet
        callback_sheet._worksheet_cache.clear()
        ws = FakeWorksheet(headers=HEADERS)

        with patch.object(callback_sheet, "_get_worksheet", return_value=ws) as mock_get:
            callback_sheet.append_callback(
                name="Anna Landry", number="6033612514", reason="wants receipt not estimate",
                callback="Not specified", is_emergency=False, email=None, call_id="call_2",
            )
            mock_get.assert_called_once_with("Non-Emergency")

        self.assertEqual(len(ws._data), 2)

    def test_same_call_id_updates_instead_of_duplicating(self):
        from dashboard_sync import callback_sheet
        callback_sheet._worksheet_cache.clear()
        ws = FakeWorksheet(headers=HEADERS)

        with patch.object(callback_sheet, "_get_worksheet", return_value=ws):
            callback_sheet.append_callback(
                name="Lorraine Finn", number="9788860923", reason="cancel stuck on invoice",
                callback="Morning", is_emergency=False, email=None, call_id="call_3",
            )
            # Retell reintenta el mismo tool call (mismo call_id, distinto texto de reason).
            callback_sheet.append_callback(
                name="Lorraine Finn", number="9788860923", reason="cancel stuck on invoice (retry)",
                callback="Morning", is_emergency=False, email=None, call_id="call_3",
            )

        self.assertEqual(len(ws._data), 2, "no debe duplicar la fila para el mismo call_id")
        row = dict(zip(HEADERS, ws._data[1]))
        self.assertEqual(row["Reason for Call"], "cancel stuck on invoice (retry)")

    def test_missing_call_id_still_appends(self):
        from dashboard_sync import callback_sheet
        callback_sheet._worksheet_cache.clear()
        ws = FakeWorksheet(headers=HEADERS)

        with patch.object(callback_sheet, "_get_worksheet", return_value=ws):
            callback_sheet.append_callback(
                name="No CallId", number="6035551234", reason="test",
                callback="Afternoon", is_emergency=False, email=None, call_id=None,
            )

        self.assertEqual(len(ws._data), 2)


if __name__ == "__main__":
    unittest.main()
