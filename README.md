# Schedule bot
### About
This is the repository of telegram bot application that provides schedule of lessons for SPbSEU university.

### Installation
To run the application you need to clone the repository:

`git clone https://github.com/smart7even/schedule-bot.git`

Then install all dependencies:

`pip3 install -r requirements.txt`

Now you need to create `.env` file in root of the project and specify key `DATABASE_URL` with your database url and key `SCHEDULE_BOT_TOKEN` with telegram bot token.

Open project root in console and make database migrations entering command `alembic upgrade head` and then fill your database running `bot_init.py` script.

Now you can use application running `main.py` script.

### Server run
To run api server in dev mode use following command

`uvicorn server:app --env-file .env --reload --host 0.0.0.0`

### Runtime feature flags

Feature flags are stored in the database and evaluated on every request, so a
change does not require an API restart. They default to `false` if configuration
storage is unavailable.

The public read-only configuration is available at `GET /app/config`. Change a
flag from an authenticated server shell instead of exposing an admin web page:

```sh
python3 manage_feature_flags.py list
python3 manage_feature_flags.py set room_map_button_enabled false
python3 manage_feature_flags.py set room_map_caption_enabled false
```

Only the flags listed by the command are accepted. Each write records its
database update time.

### Observability

The backend provides separate `GET /health/live` and `GET /health/ready`
probes, writes structured JSON logs, and exports bounded HTTP metrics through
standard OTLP when a collector endpoint is configured. See
[`docs/observability.md`](docs/observability.md) for the event schema, privacy
constraints, and local collector setup.

### Live schedule sampling

Before a backend release that changes schedule parsing, run a reproducible
sample against the current university HTML:

```sh
python scripts/audit_live_schedules.py --sample-size 12 --seed 2026-09-24 --group-id 13863
```

The script first covers different faculties and courses, then fills the sample
randomly. It prints the seed and group IDs so a failure can be reproduced. It
checks room, building, note, and room-map links independently of the parser.
After deploying the backend, repeat the same sample with `--check-api` to
compare the public response as well. Use a new seed for each release; include
any reported group with `--group-id` while investigating it. An automated
GitHub Actions run performs a new source/parser sample each Wednesday. It does
not change university data or production configuration.

### Remote app configuration

`GET /app/config` also evaluates the versioned `mobile_app` configuration.
Each parameter has a default JSON value and an ordered list of rules. Rules are
checked from top to bottom and the first matching rule wins for that parameter.
All conditions inside one rule use AND semantics; use multiple ordered rules
to express OR. Unknown parameters remain available as JSON payloads and are
ignored safely by clients that do not understand them.

The evaluator accepts only bounded, allowlisted attributes and operators:

- server-resolved `group.id`, `group.course`, and `group.faculty_id`;
- server-owned `request.time_msk` and `request.weekday_msk`;
- client-declared `client.platform` and `client.version`;
- `equals`, `not_equals`, `in`, `not_in`, and half-open
  `time_between` ranges (`start <= time < end`, including overnight ranges).

There is no public write endpoint. Validate and preview a candidate from an
authenticated server shell before publishing it atomically:

```sh
python3 manage_remote_config.py validate remote_config.example.json
python3 manage_remote_config.py evaluate --file remote_config.example.json \
  --group-id 13872 --at 2026-09-16T10:00:00+03:00
python3 manage_remote_config.py set remote_config.example.json
python3 manage_remote_config.py show
python3 manage_remote_config.py history
python3 manage_remote_config.py rollback 1
```

Every publish creates an immutable revision. Rollback republishes an earlier
document as a new revision, preserving the audit trail. The public endpoint
returns the resolved payload, revision, and a bounded client refresh interval;
rule identifiers and the rule document remain server-side.

### Telemetry routing

The `telemetry` remote parameter accepts `{"mode":"appmetrica"}`, `{"mode":"off"}`,
or `{"mode":"sentry","sentry_dsn":"https://PUBLIC_KEY@sentry.roadmapik.com/PROJECT_ID"}`
(`both` sends to both providers). The collector host is allowlisted on server and
client. Include this object as a parameter's `default` or rule `value`; publish
with `manage_remote_config.py set FILE`, inspect with `show`/`history`, or use
`rollback REVISION`. Revisions are immutable; rollback creates a new revision.
The new client polls every five minutes (configurable 60–3600 seconds), uses its
last valid cached config on restart, and retains it during outages. Older clients
ignore these additive fields and continue using AppMetrica.
