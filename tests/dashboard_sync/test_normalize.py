# tests/dashboard_sync/test_normalize.py
import json
import unittest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ExtractNormalCallTests(unittest.TestCase):
    def setUp(self):
        from dashboard_sync import normalize
        self.normalize = normalize
        self.call = _load("call_normal.json")

    def test_basic_fields(self):
        result = self.normalize.extract(self.call)
        self.assertEqual(result["call_id"], "call_normal_001")
        self.assertEqual(result["duration_s"], 68)
        self.assertEqual(result["direction"], "inbound")
        self.assertEqual(result["from_number"], "+15185551234")
        self.assertEqual(result["to_number"], "+18005551000")

    def test_day_and_start_time_are_eastern(self):
        result = self.normalize.extract(self.call)
        self.assertEqual(result["day"], "2026-07-08")
        self.assertEqual(result["start_time"], "10:00")

    def test_call_analysis_fields(self):
        result = self.normalize.extract(self.call)
        self.assertTrue(result["call_successful"])
        self.assertEqual(result["sentiment"], "Positive")
        self.assertEqual(result["intent"], "new_booking")
        self.assertEqual(result["service_type"], "plumbing")
        self.assertTrue(result["action_completed"])
        self.assertEqual(result["summary"], "Customer booked a plumbing appointment for tomorrow morning.")

    def test_cost_per_minute(self):
        result = self.normalize.extract(self.call)
        self.assertEqual(result["cost_cents"], 42)
        self.assertAlmostEqual(result["cost_per_min_cents"], 37.06, places=2)

    def test_not_spam_not_stalled(self):
        result = self.normalize.extract(self.call)
        self.assertFalse(result["is_spam"])
        self.assertFalse(result["is_stalled"])

    def test_no_failed_tools(self):
        result = self.normalize.extract(self.call)
        self.assertEqual(result["failed_tools"], [])


class ExtractSpamCallTests(unittest.TestCase):
    def test_flagged_as_spam(self):
        from dashboard_sync import normalize
        call = _load("call_spam.json")
        result = normalize.extract(call)
        self.assertTrue(result["is_spam"])
        self.assertEqual(result["duration_s"], 15)

    def test_zero_duration_cost_per_minute_does_not_divide_by_zero(self):
        from dashboard_sync import normalize
        call = _load("call_spam.json")
        call["duration_ms"] = 0
        result = normalize.extract(call)
        self.assertEqual(result["cost_per_min_cents"], 0)


class ExtractFailedToolCallTests(unittest.TestCase):
    def setUp(self):
        from dashboard_sync import normalize
        self.normalize = normalize
        self.call = _load("call_failed_tool.json")

    def test_failed_tools_listed(self):
        result = self.normalize.extract(self.call)
        self.assertEqual(result["failed_tools"], ["create_job"])

    def test_flagged_as_stalled_due_to_trailing_silence(self):
        result = self.normalize.extract(self.call)
        self.assertTrue(result["is_stalled"])

    def test_not_flagged_as_spam_because_duration_over_threshold(self):
        result = self.normalize.extract(self.call)
        self.assertFalse(result["is_spam"])


class ExtractMalformedToolCallTests(unittest.TestCase):
    def test_failed_tool_without_name_is_skipped_not_crashing(self):
        from dashboard_sync import normalize
        call = {
            "tool_calls": [
                {"success": False},  # malformed: no "name"
                {"name": "create_job", "success": False},
            ],
        }
        result = normalize.extract(call)
        self.assertEqual(result["failed_tools"], ["create_job"])


if __name__ == "__main__":
    unittest.main()
