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


if __name__ == "__main__":
    unittest.main()
