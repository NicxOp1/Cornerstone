import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or json.dumps(self._payload)

    def json(self):
        return self._payload


class FakeAsyncClient:
    post_calls = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers=None):
        return FakeResponse(
            payload={
                "data": [
                    {
                        "id": 30,
                        "businessUnitIds": [40],
                    }
                ]
            }
        )

    async def post(self, url, headers=None, json=None):
        self.__class__.post_calls.append({"url": url, "headers": headers, "json": json})
        return FakeResponse(payload={"id": 123, "lastAppointmentId": 456})


class BackendRuntimeTests(unittest.TestCase):
    def setUp(self):
        main.idempotency_cache.clear()
        main.idempotency_locks.clear()
        main.call_sessions.clear()
        FakeAsyncClient.post_calls = []
        self.client = TestClient(main.app)

    def tearDown(self):
        main.idempotency_cache.clear()
        main.idempotency_locks.clear()
        main.call_sessions.clear()

    def test_massachusetts_to_utc_handles_dst(self):
        self.assertEqual(main.massachusetts_to_utc("2026-01-15T09:00:00Z"), "2026-01-15T14:00:00Z")
        self.assertEqual(main.massachusetts_to_utc("2026-07-15T09:00:00Z"), "2026-07-15T13:00:00Z")

    def test_send_office_message_is_idempotent_per_call_id_and_args(self):
        payload = {
            "args": {
                "name": "Jane Caller",
                "number": "15551234567",
                "reason": "Needs callback",
                "callback": "Afternoon",
                "isEmergency": False,
            },
            "call": {"call_id": "call-send-office-1"},
        }

        sent = []

        def fake_send(subject, body, html_body=None):
            sent.append((subject, body))
            return True

        with patch.object(main, "_send_gmail", side_effect=fake_send):
            first = self.client.post("/sendOfficeMessage", json=payload)
            second = self.client.post("/sendOfficeMessage", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(len(sent), 1)

    def test_create_job_uses_idempotency_and_keeps_single_servicetitan_post(self):
        payload = {
            "args": {
                "customerId": 10,
                "locationId": 20,
                "jobTypeId": 30,
                "priority": "Normal",
                "businessUnitId": 40,
                "campaignId": 50,
                "jobStartTime": "2026-07-15T09:00:00Z",
                "jobEndTime": "2026-07-15T12:00:00Z",
                "summary": "Customer requested standard electrical service.",
            },
            "call": {"call_id": "call-create-job-1"},
        }

        async def fake_token():
            return "Bearer test-token"

        with patch.object(main, "get_access_token", side_effect=fake_token):
            with patch.object(main.httpx, "AsyncClient", FakeAsyncClient):
                first = self.client.post("/createJob", json=payload)
                second = self.client.post("/createJob", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["jobId"], 123)
        self.assertEqual(second.json()["jobId"], 123)
        self.assertEqual(len(FakeAsyncClient.post_calls), 1)
        sent_payload = FakeAsyncClient.post_calls[0]["json"]
        self.assertEqual(sent_payload["appointments"][0]["start"], "2026-07-15T13:00:00Z")
        self.assertEqual(sent_payload["appointments"][0]["end"], "2026-07-15T16:00:00Z")


if __name__ == "__main__":
    unittest.main()
