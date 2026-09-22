import json
import os
import unittest
from unittest.mock import MagicMock, patch

from ops.synthetic_check import index


def _response(status: int, body: dict):
    response = MagicMock()
    response.status = status
    response.read.return_value = json.dumps(body).encode()
    response.__enter__.return_value = response
    return response


class SyntheticCheckTest(unittest.TestCase):
    @patch.dict(os.environ, {"TARGET_BASE_URL": "https://example.test/"})
    def test_handler_checks_all_public_paths(self):
        responses = [
            _response(200, {"status": "ok"}),
            _response(200, {"status": "ready"}),
            _response(200, {"recommended": {}, "calendar_current": {}}),
        ]

        with patch.object(
            index.urllib.request,
            "urlopen",
            side_effect=responses,
        ) as open_:
            result = index.handler({}, None)

        self.assertTrue(result["ok"])
        self.assertEqual(
            [item["path"] for item in result["checks"]],
            ["/health/live", "/health/ready", "/schedule/context"],
        )
        self.assertTrue(
            all(call.kwargs["timeout"] == 5 for call in open_.call_args_list)
        )

    @patch.dict(os.environ, {"TARGET_BASE_URL": "https://example.test"})
    def test_handler_fails_without_leaking_exception_message(self):
        with patch.object(
            index.urllib.request,
            "urlopen",
            side_effect=OSError("private target detail"),
        ), patch("builtins.print") as print_:
            with self.assertRaisesRegex(
                RuntimeError,
                "external health check failed",
            ):
                index.handler({}, None)

        output = print_.call_args.args[0]
        self.assertIn('"error_type":"OSError"', output)
        self.assertNotIn("private target detail", output)
        self.assertNotIn("example.test", output)
