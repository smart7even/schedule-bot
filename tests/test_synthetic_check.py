import json
from unittest.mock import MagicMock, patch

import pytest

from ops.synthetic_check import index


def _response(status: int, body: dict):
    response = MagicMock()
    response.status = status
    response.read.return_value = json.dumps(body).encode()
    response.__enter__.return_value = response
    return response


def test_handler_checks_all_public_paths(monkeypatch):
    monkeypatch.setenv("TARGET_BASE_URL", "https://example.test/")
    responses = [
        _response(200, {"status": "ok"}),
        _response(200, {"status": "ready"}),
        _response(200, {"recommended": {}, "calendar_current": {}}),
    ]

    with patch.object(index.urllib.request, "urlopen", side_effect=responses) as open_:
        result = index.handler({}, None)

    assert result["ok"] is True
    assert [item["path"] for item in result["checks"]] == [
        "/health/live",
        "/health/ready",
        "/schedule/context",
    ]
    assert all(call.kwargs["timeout"] == 5 for call in open_.call_args_list)


def test_handler_fails_without_leaking_exception_message(monkeypatch, capsys):
    monkeypatch.setenv("TARGET_BASE_URL", "https://example.test")

    with patch.object(
        index.urllib.request,
        "urlopen",
        side_effect=OSError("private target detail"),
    ):
        with pytest.raises(RuntimeError, match="external health check failed"):
            index.handler({}, None)

    output = capsys.readouterr().out
    assert '"error_type":"OSError"' in output
    assert "private target detail" not in output
    assert "example.test" not in output
