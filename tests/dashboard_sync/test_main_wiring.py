import unittest

from fastapi.testclient import TestClient

import main


class WebhookRouteWiringTests(unittest.TestCase):
    def test_call_synced_route_is_registered_on_the_main_app(self):
        client = TestClient(main.app)

        resp = client.post("/webhooks/callSynced", json={"call_id": "call_x"})

        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
    unittest.main()
