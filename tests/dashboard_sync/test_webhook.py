import unittest
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_test_app():
    from dashboard_sync import webhook

    app = FastAPI()
    app.include_router(webhook.router)
    return app


class TokenAuthTests(unittest.TestCase):
    @patch("dashboard_sync.webhook.config")
    def test_missing_token_returns_401(self, mock_config):
        mock_config.DASHBOARD_SYNC_TOKEN = "secret-token"
        client = TestClient(_build_test_app())

        resp = client.post("/webhooks/callSynced", json={"call": {"call_id": "call_1"}})

        self.assertEqual(resp.status_code, 401)

    @patch("dashboard_sync.webhook.config")
    def test_wrong_token_returns_401(self, mock_config):
        mock_config.DASHBOARD_SYNC_TOKEN = "secret-token"
        client = TestClient(_build_test_app())

        resp = client.post("/webhooks/callSynced?token=wrong", json={"call": {"call_id": "call_1"}})

        self.assertEqual(resp.status_code, 401)


class PayloadParsingTests(unittest.TestCase):
    @patch("dashboard_sync.webhook.pipeline.process_call", new_callable=AsyncMock)
    @patch("dashboard_sync.webhook._get_sheets_client")
    @patch("dashboard_sync.webhook.config")
    def test_wrapped_event_payload_is_accepted(self, mock_config, mock_get_sheets, mock_process_call):
        mock_config.DASHBOARD_SYNC_TOKEN = "secret-token"
        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_process_call.return_value = {"call_id": "call_1"}
        client = TestClient(_build_test_app())

        resp = client.post(
            "/webhooks/callSynced?token=secret-token",
            json={"event": "call_analyzed", "call": {"call_id": "call_1"}},
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok", "call_id": "call_1"})
        mock_process_call.assert_awaited_once()

    @patch("dashboard_sync.webhook.pipeline.process_call", new_callable=AsyncMock)
    @patch("dashboard_sync.webhook._get_sheets_client")
    @patch("dashboard_sync.webhook.config")
    def test_raw_call_object_without_wrapper_is_accepted(self, mock_config, mock_get_sheets, mock_process_call):
        mock_config.DASHBOARD_SYNC_TOKEN = "secret-token"
        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_process_call.return_value = {"call_id": "call_2"}
        client = TestClient(_build_test_app())

        resp = client.post(
            "/webhooks/callSynced?token=secret-token",
            json={"call_id": "call_2", "duration_ms": 1000},
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok", "call_id": "call_2"})

    @patch("dashboard_sync.webhook.config")
    def test_payload_without_identifiable_call_id_returns_422(self, mock_config):
        mock_config.DASHBOARD_SYNC_TOKEN = "secret-token"
        client = TestClient(_build_test_app())

        resp = client.post("/webhooks/callSynced?token=secret-token", json={"event": "call_analyzed"})

        self.assertEqual(resp.status_code, 422)


class DownstreamFailureTests(unittest.TestCase):
    @patch("dashboard_sync.webhook.pipeline.process_call", new_callable=AsyncMock)
    @patch("dashboard_sync.webhook._get_sheets_client")
    @patch("dashboard_sync.webhook.config")
    def test_pipeline_exception_still_returns_200_with_error_status(self, mock_config, mock_get_sheets, mock_process_call):
        mock_config.DASHBOARD_SYNC_TOKEN = "secret-token"
        mock_config.BLOB_READ_WRITE_TOKEN = "blob-token"
        mock_process_call.side_effect = Exception("Sheets caido")
        client = TestClient(_build_test_app())

        resp = client.post(
            "/webhooks/callSynced?token=secret-token",
            json={"call_id": "call_3"},
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "error", "call_id": "call_3"})


if __name__ == "__main__":
    unittest.main()
