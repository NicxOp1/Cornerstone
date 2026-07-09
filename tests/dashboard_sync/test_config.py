# tests/dashboard_sync/test_config.py
import importlib
import json
import os
import unittest
from unittest.mock import patch


class ConfigTests(unittest.TestCase):
    def test_google_service_account_info_parses_json_env_var(self):
        fake_json = json.dumps({"client_email": "x@y.iam.gserviceaccount.com", "private_key": "abc"})
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": fake_json}):
            from dashboard_sync import config
            importlib.reload(config)
            info = config.google_service_account_info()
        self.assertEqual(info["client_email"], "x@y.iam.gserviceaccount.com")

    def test_missing_env_vars_default_to_empty_string(self):
        with patch.dict(os.environ, {}, clear=True):
            from dashboard_sync import config
            importlib.reload(config)
            self.assertEqual(config.DASHBOARD_SYNC_TOKEN, "")
            self.assertEqual(config.GOOGLE_SHEET_ID, "")


if __name__ == "__main__":
    unittest.main()
