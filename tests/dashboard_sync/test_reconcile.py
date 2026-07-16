import time
import unittest
from unittest.mock import MagicMock, patch


class FilterUnsyncedTests(unittest.TestCase):
    def test_removes_calls_already_in_the_sheet(self):
        from dashboard_sync import reconcile

        calls = [{"call_id": "a"}, {"call_id": "b"}, {"call_id": "c"}]

        result = reconcile.filter_unsynced(calls, already_synced_ids={"a", "c"})

        self.assertEqual([c["call_id"] for c in result], ["b"])

    def test_ignores_calls_without_call_id(self):
        from dashboard_sync import reconcile

        calls = [{"call_id": "a"}, {"no_id": True}]

        result = reconcile.filter_unsynced(calls, already_synced_ids=set())

        self.assertEqual([c["call_id"] for c in result], ["a"])


class FetchRecentCallsTests(unittest.TestCase):
    @patch("dashboard_sync.reconcile.requests.post")
    @patch("dashboard_sync.reconcile.config")
    def test_single_page_response(self, mock_config, mock_post):
        from dashboard_sync import reconcile

        mock_config.RETELL_API_KEY = "fake-key"
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = [{"call_id": "a"}, {"call_id": "b"}]
        mock_post.return_value.raise_for_status = lambda: None

        result = reconcile.fetch_recent_calls(lookback_hours=48)

        self.assertEqual([c["call_id"] for c in result], ["a", "b"])

    @patch("dashboard_sync.reconcile.requests.post")
    @patch("dashboard_sync.reconcile.config")
    def test_follows_pagination(self, mock_config, mock_post):
        from dashboard_sync import reconcile

        mock_config.RETELL_API_KEY = "fake-key"
        first_page = MagicMock(status_code=200)
        first_page.json.return_value = {
            "items": [{"call_id": "a"}],
            "has_more": True,
            "pagination_key": "next",
        }
        first_page.raise_for_status = lambda: None
        second_page = MagicMock(status_code=200)
        second_page.json.return_value = {"items": [{"call_id": "b"}], "has_more": False}
        second_page.raise_for_status = lambda: None
        mock_post.side_effect = [first_page, second_page]

        result = reconcile.fetch_recent_calls(lookback_hours=48)

        self.assertEqual([c["call_id"] for c in result], ["a", "b"])
        self.assertEqual(mock_post.call_count, 2)


class RunTests(unittest.IsolatedAsyncioTestCase):
    @patch("dashboard_sync.reconcile.pipeline.process_call")
    @patch("dashboard_sync.reconcile.sheets_client.connect")
    @patch("dashboard_sync.reconcile.fetch_recent_calls")
    @patch("dashboard_sync.reconcile.config")
    async def test_only_processes_calls_not_yet_in_the_sheet(
        self,
        mock_config,
        mock_fetch,
        mock_connect,
        mock_process_call,
    ):
        from unittest.mock import AsyncMock
        from dashboard_sync import reconcile

        mock_config.GOOGLE_SHEET_ID = "sheet-1"
        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_config.google_service_account_info = lambda: {}
        mock_fetch.return_value = [{"call_id": "a"}, {"call_id": "b"}]
        fake_sheets = MagicMock()
        fake_sheets.get_existing_call_ids.return_value = ["a"]
        mock_connect.return_value = fake_sheets
        mock_process_call.side_effect = AsyncMock()

        await reconcile.run()

        mock_process_call.assert_called_once()
        called_call = mock_process_call.call_args.args[0]
        self.assertEqual(called_call["call_id"], "b")

    @patch("dashboard_sync.reconcile.pipeline.process_call")
    @patch("dashboard_sync.reconcile.sheets_client.connect")
    @patch("dashboard_sync.reconcile.fetch_recent_calls")
    @patch("dashboard_sync.reconcile.config")
    async def test_passes_custom_lookback_hours_to_fetch(
        self,
        mock_config,
        mock_fetch,
        mock_connect,
        mock_process_call,
    ):
        from dashboard_sync import reconcile

        mock_config.GOOGLE_SHEET_ID = "sheet-1"
        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_config.google_service_account_info = lambda: {}
        mock_fetch.return_value = []
        fake_sheets = MagicMock()
        fake_sheets.get_existing_call_ids.return_value = []
        mock_connect.return_value = fake_sheets

        await reconcile.run(lookback_hours=96)

        mock_fetch.assert_called_once_with(96)

    @patch("dashboard_sync.reconcile.pipeline.process_call")
    @patch("dashboard_sync.reconcile.fetch_recent_calls")
    @patch("dashboard_sync.reconcile.config")
    async def test_run_returns_summary_and_reuses_injected_sheets(
        self,
        mock_config,
        mock_fetch,
        mock_process_call,
    ):
        from unittest.mock import AsyncMock
        from dashboard_sync import reconcile

        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_config.RECONCILE_LOOKBACK_HOURS = 3
        mock_fetch.return_value = [{"call_id": "a"}, {"call_id": "b"}]
        fake_sheets = MagicMock()
        fake_sheets.get_existing_call_ids.return_value = ["a"]
        mock_process_call.side_effect = AsyncMock()

        summary = await reconcile.run(sheets=fake_sheets)

        self.assertEqual(
            summary,
            {"scanned": 2, "pending": 1, "synced": 1, "errors": 0, "deferred": 0, "capped": 0},
        )
        mock_process_call.assert_called_once()

    @patch("dashboard_sync.reconcile.pipeline.process_call")
    @patch("dashboard_sync.reconcile.fetch_recent_calls")
    @patch("dashboard_sync.reconcile.config")
    async def test_caps_calls_processed_per_run(
        self,
        mock_config,
        mock_fetch,
        mock_process_call,
    ):
        # Si hay mas pendientes que RECONCILE_MAX_PER_RUN, esta corrida solo
        # procesa el tope -- el resto queda para la proxima (el pipeline es
        # idempotente, así que no hay riesgo de perderlas). Esto es lo que
        # evita que una racha de llamadas sin sincronizar haga que la corrida
        # tarde tanto que el proxy de Render la corte (ver config.py).
        from unittest.mock import AsyncMock
        from dashboard_sync import reconcile

        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_config.RECONCILE_LOOKBACK_HOURS = 3
        mock_config.RECONCILE_MAX_PER_RUN = 2
        mock_fetch.return_value = [{"call_id": c} for c in ["a", "b", "c", "d"]]
        fake_sheets = MagicMock()
        fake_sheets.get_existing_call_ids.return_value = []
        mock_process_call.side_effect = AsyncMock()

        summary = await reconcile.run(sheets=fake_sheets)

        self.assertEqual(
            summary,
            {"scanned": 4, "pending": 4, "synced": 2, "errors": 0, "deferred": 0, "capped": 2},
        )
        self.assertEqual(mock_process_call.call_count, 2)

    @patch("dashboard_sync.reconcile.pipeline.process_call")
    @patch("dashboard_sync.reconcile.fetch_recent_calls")
    @patch("dashboard_sync.reconcile.config")
    async def test_skips_calls_whose_post_call_analysis_isnt_ready_yet(
        self, mock_config, mock_fetch, mock_process_call
    ):
        # Si Retell todavia no termino el post-call analysis, sincronizar ahora
        # deja summary/call_successful vacios para siempre (el call_id ya queda
        # "synced" y nadie lo revisita). Mejor esperar a que el cron pase de
        # nuevo dentro de la ventana de gracia.
        from unittest.mock import AsyncMock
        from dashboard_sync import reconcile

        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_config.RECONCILE_LOOKBACK_HOURS = 3
        mock_config.RECONCILE_MAX_PER_RUN = 10
        mock_fetch.return_value = [
            {"call_id": "fresh-no-analysis", "end_timestamp": time.time() * 1000},
            {
                "call_id": "ready",
                "end_timestamp": time.time() * 1000,
                "call_analysis": {"call_summary": "done"},
            },
        ]
        fake_sheets = MagicMock()
        fake_sheets.get_existing_call_ids.return_value = []
        mock_process_call.side_effect = AsyncMock()

        summary = await reconcile.run(sheets=fake_sheets)

        mock_process_call.assert_called_once()
        self.assertEqual(mock_process_call.call_args.args[0]["call_id"], "ready")
        self.assertEqual(summary["deferred"], 1)
        self.assertEqual(summary["synced"], 1)

    @patch("dashboard_sync.reconcile.pipeline.process_call")
    @patch("dashboard_sync.reconcile.fetch_recent_calls")
    @patch("dashboard_sync.reconcile.config")
    async def test_syncs_old_call_anyway_even_without_analysis(
        self, mock_config, mock_fetch, mock_process_call
    ):
        # Si el analisis nunca llega (caso raro), no queremos que la llamada
        # quede diferida para siempre y se caiga de la ventana de lookback sin
        # sincronizarse nunca -- pasada la ventana de gracia, se sincroniza
        # igual con lo que haya.
        from unittest.mock import AsyncMock
        from dashboard_sync import reconcile

        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_config.RECONCILE_LOOKBACK_HOURS = 3
        mock_config.RECONCILE_MAX_PER_RUN = 10
        old_end_ms = (time.time() - 3600) * 1000
        mock_fetch.return_value = [{"call_id": "stale-no-analysis", "end_timestamp": old_end_ms}]
        fake_sheets = MagicMock()
        fake_sheets.get_existing_call_ids.return_value = []
        mock_process_call.side_effect = AsyncMock()

        summary = await reconcile.run(sheets=fake_sheets)

        mock_process_call.assert_called_once()
        self.assertEqual(summary["deferred"], 0)
        self.assertEqual(summary["synced"], 1)


class ShouldDeferTests(unittest.TestCase):
    def test_defers_recent_call_without_analysis(self):
        from dashboard_sync import reconcile

        recent_call = {"call_id": "x", "end_timestamp": time.time() * 1000}

        self.assertTrue(reconcile._should_defer(recent_call))

    def test_does_not_defer_when_analysis_is_ready(self):
        from dashboard_sync import reconcile

        call = {
            "call_id": "x",
            "end_timestamp": time.time() * 1000,
            "call_analysis": {"call_summary": "done"},
        }

        self.assertFalse(reconcile._should_defer(call))

    def test_does_not_defer_call_missing_end_timestamp(self):
        from dashboard_sync import reconcile

        self.assertFalse(reconcile._should_defer({"call_id": "x"}))

    def test_does_not_defer_call_older_than_the_grace_window(self):
        from dashboard_sync import reconcile

        old_call = {"call_id": "x", "end_timestamp": (time.time() - 3600) * 1000}

        self.assertFalse(reconcile._should_defer(old_call))


if __name__ == "__main__":
    unittest.main()
