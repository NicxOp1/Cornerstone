import unittest
from unittest.mock import MagicMock, patch


class UploadRecordingTests(unittest.TestCase):
    @patch("dashboard_sync.blob_storage.requests.put")
    @patch("dashboard_sync.blob_storage.requests.get")
    def test_downloads_and_uploads_recording(self, mock_get, mock_put):
        from dashboard_sync import blob_storage

        mock_get.return_value = MagicMock(status_code=200, content=b"fake-wav-bytes")
        mock_get.return_value.raise_for_status = lambda: None
        mock_put.return_value = MagicMock(status_code=200)
        mock_put.return_value.json.return_value = {"url": "https://blob.example.com/recordings/call_1.wav"}

        result = blob_storage.upload_recording("call_1", "https://cloudfront.example/recording.wav", "fake-token")

        self.assertEqual(result, "https://blob.example.com/recordings/call_1.wav")
        mock_put.assert_called_once()
        put_kwargs = mock_put.call_args
        self.assertIn("recordings/call_1.wav", put_kwargs.args[0])
        self.assertEqual(put_kwargs.kwargs["headers"]["Authorization"], "Bearer fake-token")

    @patch("dashboard_sync.blob_storage.requests.get")
    def test_returns_none_when_recording_download_fails(self, mock_get):
        from dashboard_sync import blob_storage
        import requests

        mock_get.side_effect = requests.RequestException("404 not found")

        result = blob_storage.upload_recording("call_1", "https://cloudfront.example/gone.wav", "fake-token")

        self.assertIsNone(result)

    @patch("dashboard_sync.blob_storage.requests.put")
    @patch("dashboard_sync.blob_storage.requests.get")
    def test_returns_none_when_blob_upload_fails(self, mock_get, mock_put):
        from dashboard_sync import blob_storage

        mock_get.return_value = MagicMock(status_code=200, content=b"fake-wav-bytes")
        mock_get.return_value.raise_for_status = lambda: None
        mock_put.return_value = MagicMock(status_code=500, text="internal error")

        result = blob_storage.upload_recording("call_1", "https://cloudfront.example/recording.wav", "fake-token")

        self.assertIsNone(result)


class UploadTranscriptTests(unittest.TestCase):
    @patch("dashboard_sync.blob_storage.requests.put")
    def test_uploads_transcript_as_json(self, mock_put):
        from dashboard_sync import blob_storage

        mock_put.return_value = MagicMock(status_code=200)
        mock_put.return_value.json.return_value = {"url": "https://blob.example.com/transcripts/call_1.json"}

        result = blob_storage.upload_transcript("call_1", [{"role": "agent", "content": "hi"}], "fake-token")

        self.assertEqual(result, "https://blob.example.com/transcripts/call_1.json")
        put_kwargs = mock_put.call_args
        self.assertEqual(put_kwargs.kwargs["headers"]["x-content-type"], "application/json")

    @patch("dashboard_sync.blob_storage.requests.put")
    def test_returns_none_on_upload_error(self, mock_put):
        from dashboard_sync import blob_storage

        mock_put.return_value = MagicMock(status_code=500, text="internal error")

        result = blob_storage.upload_transcript("call_1", [], "fake-token")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
