import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Optional


_STANDARD_LOG_FIELDS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName",
}


class JsonFormatter(logging.Formatter):
    """Render one safe, machine-readable JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in _STANDARD_LOG_FIELDS:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class _ApplicationTelemetryOnly(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name in {
            "schedule-api",
            "schedule-maintenance",
            "schedule-observability",
        }


_configured = False
_meter = None


def configure_observability(service_name: str) -> None:
    """Configure JSON stdout and optional standard OTLP export.

    Export is fail-open and enabled only when OTEL_EXPORTER_OTLP_ENDPOINT is
    present. The application has no provider-specific endpoint or credential.
    """
    global _configured, _meter
    if _configured:
        return

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(JsonFormatter())
    root.addHandler(stdout_handler)

    # Uvicorn installs its own plain-text handlers before importing the app.
    # Route them through the same formatter so raw URLs and tracebacks are not
    # emitted by a second logging path.
    for logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.disabled = True

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry import metrics
            from opentelemetry.exporter.otlp.proto.http._log_exporter import (
                OTLPLogExporter,
            )
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import (
                PeriodicExportingMetricReader,
            )
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({
                "service.name": service_name,
                "deployment.environment.name": os.getenv(
                    "DEPLOYMENT_ENVIRONMENT", "production"
                ),
            })

            logger_provider = LoggerProvider(resource=resource)
            logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(OTLPLogExporter())
            )
            otel_handler = LoggingHandler(
                level=root.level,
                logger_provider=logger_provider,
            )
            otel_handler.addFilter(_ApplicationTelemetryOnly())
            root.addHandler(otel_handler)

            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(),
                export_interval_millis=int(
                    os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60000")
                ),
            )
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
            metrics.set_meter_provider(meter_provider)
            _meter = metrics.get_meter("schedule-bot")
        except Exception:
            logging.getLogger("schedule-observability").exception(
                "OTLP initialization failed; continuing with stdout logs",
                extra={"event": "telemetry.initialization_failed"},
            )

    _configured = True


class HttpMetrics:
    def __init__(self):
        self._requests = None
        self._duration = None
        if _meter is not None:
            self._requests = _meter.create_counter(
                "schedule.http.server.requests",
                unit="{request}",
                description="HTTP requests handled by the schedule API",
            )
            self._duration = _meter.create_histogram(
                "schedule.http.server.duration",
                unit="ms",
                description="Schedule API request duration",
            )

    def record(
        self,
        method: str,
        route: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        if self._requests is None or self._duration is None:
            return
        attributes = {
            "http.request.method": method,
            "http.route": route,
            "http.response.status_class": f"{status_code // 100}xx",
        }
        self._requests.add(1, attributes)
        self._duration.record(duration_ms, attributes)


def safe_path_dimensions(path_params: Dict[str, object]) -> Dict[str, int]:
    """Keep only numeric public schedule identifiers from a request path."""
    dimensions = {}
    for key in ("group_id", "professor_id", "faculty_id"):
        value = path_params.get(key)
        try:
            if value is not None:
                dimensions[key] = int(value)
        except (TypeError, ValueError):
            continue
    return dimensions


def normalized_route(scope: Dict[str, object]) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "/unmatched"


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    fields: Optional[Dict[str, object]] = None,
    exc_info: bool = False,
) -> None:
    logger.log(
        level,
        message,
        extra={"event": event, **(fields or {})},
        exc_info=exc_info,
    )
