# Backend observability

The API and maintenance worker emit structured JSON to stdout and can export
logs and metrics over standard OTLP/HTTP. Telemetry delivery is fail-open: an
unavailable collector must not make the schedule API unavailable.

## Health endpoints

- `GET /health/live` checks the API process only and is used for container
  restart decisions.
- `GET /health/ready` checks the required database and returns `503` with a
  generic response when it is unavailable.
- `GET /health` remains as a backwards-compatible liveness alias.

## Logs and dimensions

`http.request` records include the normalized route template, status code,
duration, request ID, and numeric public schedule identifiers when present.
They never include query strings, headers, request bodies, or response bodies.
This permits group-level analysis without turning group IDs into metric labels.

Requests whose normalized path contains `group_id` are enriched from the
backend group directory with a cached metadata snapshot when available:

- `group_name`
- `group_course`
- `group_faculty_id`

The lookup is bounded, cached for one hour, and fail-open. Missing metadata or
a datastore lookup failure does not affect the request and simply omits these
optional fields. Detailed group fields remain log attributes only and must not
be added to metric labels.

## Request-usage dashboard semantics

The request-usage dashboard is built from `http.request` log records. Its core
group-schedule views should filter to normalized schedule routes and use:

- record count for backend request volume over time;
- `group_course` for course breakdowns;
- `group_name` or `group_id` for group breakdowns;
- `http_status_code` for success/error views;
- `duration_ms` for latency views where the telemetry backend supports numeric
  log aggregation.

These values are backend requests, not unique users. They exclude schedule
views served entirely from the mobile cache and may include several refreshes
from one installation. Keep that interpretation visible next to the dashboard.
The structured field contract is provider-neutral, so the same records can be
exported to another log store or analytics system without changing the API.

Maintenance emits stable events for schedule observation and group sync:

- `schedule_observation.success` / `schedule_observation.failure`
- `group_sync.success` / `group_sync.failure`

Successful `/health/live` requests are omitted from logs to control volume.

Metrics use bounded labels only: HTTP method, normalized route, and status
class. The current instruments are `schedule.http.server.requests` and
`schedule.http.server.duration`.

## Collector contract

Production services send OTLP/HTTP to an OpenTelemetry Collector at
`http://otel-collector:4318`. The provider-specific collector configuration and
credentials live outside the repository. Replacing that configuration is the
only required application-independent step when changing telemetry backends.

`ops/otel-collector.example.yaml` is a credential-free local configuration
that writes received telemetry to the collector's debug exporter. Set
`OTEL_COLLECTOR_CONFIG_PATH` to an absolute private configuration path in a
deployment environment.

## External synthetic check

`ops/synthetic_check/index.py` is a provider-neutral scheduled-function
handler. It checks public liveness, readiness, and the schedule-context path,
then fails the invocation if any check fails. Configure `TARGET_BASE_URL` only
in the private deployment environment. The emitted summary contains paths,
durations, booleans, and stable error types; it does not include the target
hostname, response bodies, or exception messages.

Run the probe outside the backend's hosting failure domain. Alerting should
require consecutive failed invocations and should send a recovery notification
after the invocation becomes healthy again.
