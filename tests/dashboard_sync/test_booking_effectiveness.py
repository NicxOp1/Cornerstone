import unittest
from unittest.mock import AsyncMock, MagicMock, patch


def _twc_pair(tool_call_id, name, arguments, result_content, success=True):
    return [
        {
            "role": "tool_call_invocation",
            "tool_call_id": tool_call_id,
            "name": name,
            "arguments": arguments,
            "time_sec": 10.0,
        },
        {
            "role": "tool_call_result",
            "tool_call_id": tool_call_id,
            "successful": success,
            "content": result_content,
            "time_sec": 11.0,
        },
    ]


class NoTrackedToolsTests(unittest.IsolatedAsyncioTestCase):
    async def test_call_without_booking_tools_is_not_applicable(self):
        from dashboard_sync import booking_effectiveness

        call = {
            "transcript_with_tool_calls": [
                {
                    "role": "tool_call_invocation",
                    "tool_call_id": "tc1",
                    "name": "check_availability",
                    "arguments": "{}",
                    "time_sec": 1.0,
                }
            ]
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "not_applicable")

    async def test_call_with_no_transcript_is_not_applicable(self):
        from dashboard_sync import booking_effectiveness

        result = await booking_effectiveness.check_call({})

        self.assertEqual(result, "not_applicable")


class CreateJobConfirmedTests(unittest.IsolatedAsyncioTestCase):
    @patch("dashboard_sync.booking_effectiveness.main")
    @patch("dashboard_sync.booking_effectiveness.httpx.AsyncClient")
    async def test_confirmed_when_job_exists_with_expected_status(self, mock_client_cls, mock_main):
        from dashboard_sync import booking_effectiveness

        mock_main.get_access_token = AsyncMock(return_value="fake-token")
        mock_main.TENANT_ID = "tenant-1"
        mock_main.APP_ID = "app-1"

        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {"data": [{"id": 171326336, "jobStatus": "Scheduled"}]}
        mock_client = AsyncMock()
        mock_client.get.return_value = fake_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "create_job",
                "{\"jobTypeId\":5879699}",
                "{\"status\":\"Job booked\",\"jobId\":171326336,\"appointmentId\":171326337}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "confirmed")

    @patch("dashboard_sync.booking_effectiveness.main")
    @patch("dashboard_sync.booking_effectiveness.httpx.AsyncClient")
    async def test_mismatch_when_job_not_found_in_servicetitan(self, mock_client_cls, mock_main):
        from dashboard_sync import booking_effectiveness

        mock_main.get_access_token = AsyncMock(return_value="fake-token")
        mock_main.TENANT_ID = "tenant-1"
        mock_main.APP_ID = "app-1"

        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {"data": []}
        mock_client = AsyncMock()
        mock_client.get.return_value = fake_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "create_job",
                "{\"jobTypeId\":5879699}",
                "{\"status\":\"Job booked\",\"jobId\":171326336,\"appointmentId\":171326337}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "mismatch")


class CreateCustomerTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmed_when_customer_id_is_present(self):
        from dashboard_sync import booking_effectiveness

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "create_customer",
                "{\"name\":\"Jane Doe\"}",
                "{\"customerId\":123,\"locationId\":456,\"status\":\"created\"}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "confirmed")

    async def test_confirmed_even_when_tool_result_marks_unsuccessful_if_customer_id_is_present(self):
        from dashboard_sync import booking_effectiveness

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "create_customer",
                "{\"name\":\"Jane Doe\"}",
                "{\"customerId\":123,\"locationId\":456,\"status\":\"created\"}",
                success=False,
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "confirmed")


class CreateLocationTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmed_when_location_id_is_present(self):
        from dashboard_sync import booking_effectiveness

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "create_location",
                "{\"customerId\":123}",
                "{\"message\":\"Location created\",\"locationId\":456}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "confirmed")


class RescheduleAppointmentTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmed_when_appointment_id_is_present_in_arguments(self):
        from dashboard_sync import booking_effectiveness

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "reschedule_appointment",
                "{\"appointmentId\":171326337,\"start\":\"2026-07-01T10:00:00\"}",
                "{\"message\":\"Appointment rescheduled successfully\"}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "confirmed")


class CancelAppointmentTests(unittest.IsolatedAsyncioTestCase):
    @patch("dashboard_sync.booking_effectiveness.main")
    @patch("dashboard_sync.booking_effectiveness.httpx.AsyncClient")
    async def test_confirmed_when_job_is_canceled(self, mock_client_cls, mock_main):
        from dashboard_sync import booking_effectiveness

        mock_main.get_access_token = AsyncMock(return_value="fake-token")
        mock_main.TENANT_ID = "tenant-1"
        mock_main.APP_ID = "app-1"

        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {"data": [{"id": 171361806, "jobStatus": "Canceled"}]}
        mock_client = AsyncMock()
        mock_client.get.return_value = fake_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "cancel_appointment",
                "{\"jobId\":171361806,\"reasonId\":13510808,\"memo\":\"no longer needs it\"}",
                "{\"message\":\"Job canceled successfully\"}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "confirmed")


class ServiceTitanUnreachableTests(unittest.IsolatedAsyncioTestCase):
    @patch("dashboard_sync.booking_effectiveness.main")
    @patch("dashboard_sync.booking_effectiveness.httpx.AsyncClient")
    async def test_pending_when_servicetitan_request_fails(self, mock_client_cls, mock_main):
        from dashboard_sync import booking_effectiveness

        mock_main.get_access_token = AsyncMock(return_value="fake-token")
        mock_main.TENANT_ID = "tenant-1"
        mock_main.APP_ID = "app-1"

        mock_client = AsyncMock()
        mock_client.get.side_effect = booking_effectiveness.httpx.RequestError("timeout")
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        call = {
            "transcript_with_tool_calls": _twc_pair(
                "tc1",
                "create_job",
                "{}",
                "{\"status\":\"Job booked\",\"jobId\":171326336,\"appointmentId\":171326337}",
            )
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "pending")


class MissingResultClassificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_mismatch_when_tracked_invocation_has_no_paired_result(self):
        from dashboard_sync import booking_effectiveness

        call = {
            "transcript_with_tool_calls": [
                {
                    "role": "tool_call_invocation",
                    "tool_call_id": "tc1",
                    "name": "create_customer",
                    "arguments": "{\"name\":\"Jane Doe\"}",
                    "time_sec": 10.0,
                }
            ]
        }

        result = await booking_effectiveness.check_call(call)

        self.assertEqual(result, "mismatch")


if __name__ == "__main__":
    unittest.main()
