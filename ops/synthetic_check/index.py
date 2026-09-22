"""External synthetic check suitable for a scheduled serverless function.

The deployment environment must define ``TARGET_BASE_URL``. The handler uses
only the Python standard library and intentionally logs a bounded summary: it
never includes response bodies, target hostnames, or exception messages.
"""

import json
import os
import time
import urllib.request
from collections.abc import Callable
from typing import Any


CHECKS: tuple[tuple[str, Callable[[dict[str, Any]], bool]], ...] = (
    ("/health/live", lambda body: body.get("status") == "ok"),
    ("/health/ready", lambda body: body.get("status") == "ready"),
    (
        "/schedule/context",
        lambda body: (
            isinstance(body.get("recommended"), dict)
            and isinstance(body.get("calendar_current"), dict)
        ),
    ),
)


def _check(
    target: str,
    path: str,
    validator: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    started = time.monotonic()
    request = urllib.request.Request(
        f"{target}{path}",
        headers={"User-Agent": "unecon-external-health/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = json.loads(response.read(65_536))
            if response.status != 200 or not validator(body):
                raise ValueError("unexpected response")
        return {
            "path": path,
            "ok": True,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
        }
    except Exception as error:  # A failed dependency must become a failed probe.
        return {
            "path": path,
            "ok": False,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
            "error_type": type(error).__name__,
        }


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Run all checks and fail the invocation when any check fails."""
    del event, context
    target = os.environ["TARGET_BASE_URL"].rstrip("/")
    results = [_check(target, path, validator) for path, validator in CHECKS]
    failed = [item["path"] for item in results if not item["ok"]]
    summary = {
        "event": "external_health_check",
        "ok": not failed,
        "checks": results,
    }
    print(json.dumps(summary, separators=(",", ":")))
    if failed:
        raise RuntimeError("external health check failed: " + ",".join(failed))
    return summary
