import unittest
from core.observability import client_request_dimensions, validated_request_id

class ClientIdentityTest(unittest.TestCase):
    def test_valid_client_hints(self):
        self.assertEqual(client_request_dimensions({
            "x-app-version": "2.0.4", "x-app-build": "67",
            "x-app-platform": "ios", "x-installation-id": "a" * 32,
        }), {"app_version": "2.0.4", "app_build": "67",
             "app_platform": "ios", "installation_id": "a" * 32})
        self.assertEqual(validated_request_id({"x-request-id": "b" * 32}), "b" * 32)

    def test_untrusted_headers_and_legacy_clients(self):
        self.assertEqual(client_request_dimensions({}), {})
        self.assertIsNone(validated_request_id({}))
        self.assertEqual(client_request_dimensions({
            "x-app-version": "2.0.4\nsecret", "x-app-build": "9" * 100,
            "x-app-platform": "private device name", "x-installation-id": "email@example.com",
            "user-agent": "private user agent", "authorization": "secret",
        }), {})
        self.assertIsNone(validated_request_id({"x-request-id": "x" * 1000}))
