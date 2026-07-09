import unittest
from unittest.mock import AsyncMock, MagicMock, patch


def _minimal_call(call_id="call_1"):
    return {
        "call_id": call_id,
        "start_timestamp": 1783605600000,
        "duration_ms": 68000,
        "recording_url": "https://cloudfront.example/rec.wav",
        "transcript_with_tool_calls": [],
        "call_analysis": {
            "call_successful": True,
            "user_sentiment": "Positive",
            "call_summary": "ok",
            "custom_analysis_data": {},
        },
        "call_cost": {"combined_cost": 10},
        "tool_calls": [],
    }


class ProcessCallHappyPathTests(unittest.IsolatedAsyncioTestCase):
    @patch("dashboard_sync.pipeline.booking_effectiveness.check_call", new_callable=AsyncMock)
    @patch("dashboard_sync.pipeline.blob_storage.upload_transcript")
    @patch("dashboard_sync.pipeline.blob_storage.upload_recording")
    async def test_writes_all_fields_including_blob_urls(
        self,
        mock_upload_recording,
        mock_upload_transcript,
        mock_check_call,
    ):
        from dashboard_sync import pipeline

        mock_upload_recording.return_value = "https://blob.example.com/recordings/call_1.wav"
        mock_upload_transcript.return_value = "https://blob.example.com/transcripts/call_1.json"
        mock_check_call.return_value = "confirmed"
        sheets = MagicMock()

        result = await pipeline.process_call(_minimal_call(), sheets, "fake-blob-token")

        self.assertEqual(result["recording_blob_url"], "https://blob.example.com/recordings/call_1.wav")
        self.assertEqual(result["transcript_blob_url"], "https://blob.example.com/transcripts/call_1.json")
        self.assertEqual(result["booking_effectiveness"], "confirmed")
        self.assertRegex(result["synced_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
        sheets.upsert_call_row.assert_called_once_with("call_1", result)


class ProcessCallPartialFailureTests(unittest.IsolatedAsyncioTestCase):
    @patch("dashboard_sync.pipeline.booking_effectiveness.check_call", new_callable=AsyncMock)
    @patch("dashboard_sync.pipeline.blob_storage.upload_transcript")
    @patch("dashboard_sync.pipeline.blob_storage.upload_recording")
    async def test_missing_recording_does_not_block_the_rest(
        self,
        mock_upload_recording,
        mock_upload_transcript,
        mock_check_call,
    ):
        from dashboard_sync import pipeline

        mock_upload_recording.return_value = None
        mock_upload_transcript.return_value = "https://blob.example.com/transcripts/call_1.json"
        mock_check_call.return_value = "not_applicable"
        sheets = MagicMock()

        result = await pipeline.process_call(_minimal_call(), sheets, "fake-blob-token")

        self.assertEqual(result["recording_blob_url"], "")
        self.assertEqual(result["transcript_blob_url"], "https://blob.example.com/transcripts/call_1.json")
        self.assertEqual(result["booking_effectiveness"], "not_applicable")
        sheets.upsert_call_row.assert_called_once_with("call_1", result)

    @patch("dashboard_sync.pipeline.booking_effectiveness.check_call", new_callable=AsyncMock)
    @patch("dashboard_sync.pipeline.blob_storage.upload_transcript")
    @patch("dashboard_sync.pipeline.blob_storage.upload_recording")
    async def test_recording_upload_exception_does_not_block_the_rest(
        self,
        mock_upload_recording,
        mock_upload_transcript,
        mock_check_call,
    ):
        from dashboard_sync import pipeline

        mock_upload_recording.side_effect = RuntimeError("blob unavailable")
        mock_upload_transcript.return_value = "https://blob.example.com/transcripts/call_1.json"
        mock_check_call.return_value = "not_applicable"
        sheets = MagicMock()

        result = await pipeline.process_call(_minimal_call(), sheets, "fake-blob-token")

        self.assertEqual(result["recording_blob_url"], "")
        self.assertEqual(result["transcript_blob_url"], "https://blob.example.com/transcripts/call_1.json")
        self.assertEqual(result["booking_effectiveness"], "not_applicable")
        sheets.upsert_call_row.assert_called_once_with("call_1", result)

    @patch("dashboard_sync.pipeline.booking_effectiveness.check_call", new_callable=AsyncMock)
    @patch("dashboard_sync.pipeline.blob_storage.upload_transcript")
    @patch("dashboard_sync.pipeline.blob_storage.upload_recording")
    async def test_transcript_upload_exception_does_not_block_the_rest(
        self,
        mock_upload_recording,
        mock_upload_transcript,
        mock_check_call,
    ):
        from dashboard_sync import pipeline

        mock_upload_recording.return_value = "https://blob.example.com/recordings/call_1.wav"
        mock_upload_transcript.side_effect = RuntimeError("blob unavailable")
        mock_check_call.return_value = "confirmed"
        sheets = MagicMock()

        result = await pipeline.process_call(_minimal_call(), sheets, "fake-blob-token")

        self.assertEqual(result["recording_blob_url"], "https://blob.example.com/recordings/call_1.wav")
        self.assertEqual(result["transcript_blob_url"], "")
        self.assertEqual(result["booking_effectiveness"], "confirmed")
        sheets.upsert_call_row.assert_called_once_with("call_1", result)

    @patch("dashboard_sync.pipeline.booking_effectiveness.check_call", new_callable=AsyncMock)
    @patch("dashboard_sync.pipeline.blob_storage.upload_transcript")
    @patch("dashboard_sync.pipeline.blob_storage.upload_recording")
    @patch("dashboard_sync.pipeline.print")
    async def test_booking_effectiveness_exception_becomes_pending(
        self,
        mock_print,
        mock_upload_recording,
        mock_upload_transcript,
        mock_check_call,
    ):
        from dashboard_sync import pipeline

        mock_upload_recording.return_value = "https://blob.example.com/recordings/call_1.wav"
        mock_upload_transcript.return_value = "https://blob.example.com/transcripts/call_1.json"
        mock_check_call.side_effect = Exception("ServiceTitan down")
        sheets = MagicMock()

        result = await pipeline.process_call(_minimal_call(), sheets, "fake-blob-token")

        self.assertEqual(result["booking_effectiveness"], "pending")
        mock_print.assert_called_once_with(
            "[dashboard_sync.pipeline] booking_effectiveness fallo para call_1: ServiceTitan down"
        )
        sheets.upsert_call_row.assert_called_once_with("call_1", result)

    @patch("dashboard_sync.pipeline.booking_effectiveness.check_call", new_callable=AsyncMock)
    @patch("dashboard_sync.pipeline.blob_storage.upload_transcript")
    @patch("dashboard_sync.pipeline.blob_storage.upload_recording")
    async def test_call_without_recording_url_skips_upload_call(
        self,
        mock_upload_recording,
        mock_upload_transcript,
        mock_check_call,
    ):
        from dashboard_sync import pipeline

        mock_upload_transcript.return_value = ""
        mock_check_call.return_value = "not_applicable"
        sheets = MagicMock()
        call = _minimal_call()
        call["recording_url"] = ""

        result = await pipeline.process_call(call, sheets, "fake-blob-token")

        mock_upload_recording.assert_not_called()
        self.assertEqual(result["recording_blob_url"], "")
        sheets.upsert_call_row.assert_called_once_with("call_1", result)


if __name__ == "__main__":
    unittest.main()
