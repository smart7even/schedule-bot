import copy
import json
import re
from urllib.parse import urlsplit
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Optional, Tuple

from core.models.group import Group


REMOTE_CONFIG_KEY = "mobile_app"
DEFAULT_REFRESH_INTERVAL_SECONDS = 300
MIN_REFRESH_INTERVAL_SECONDS = 60
MAX_REFRESH_INTERVAL_SECONDS = 3600
MAX_DOCUMENT_BYTES = 131072
MAX_PARAMETERS = 100
MAX_RULES_PER_PARAMETER = 100
MAX_CONDITIONS_PER_RULE = 10

MOSCOW_TIMEZONE = timezone(timedelta(hours=3), name="Europe/Moscow")

DEFAULT_REMOTE_CONFIG_DOCUMENT = {
    "schema_version": 1,
    "refresh_interval_seconds": DEFAULT_REFRESH_INTERVAL_SECONDS,
    "parameters": {
        "schedule_auto_scroll_today": {
            "description": "Start the current week at today's section on cold launch.",
            "default": False,
            "rules": [],
        },
    },
}

DEFAULT_REMOTE_PAYLOAD = {
    "schedule_auto_scroll_today": False,
}

_PARAMETER_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_RULE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")
_ALLOWED_ATTRIBUTES = {
    "group.id": int,
    "group.course": int,
    "group.faculty_id": int,
    "request.weekday_msk": int,
    "request.time_msk": str,
    "client.platform": str,
    "client.version": str,
}
_SET_OPERATORS = {"equals", "not_equals", "in", "not_in"}
_RESERVED_PARAMETERS = {
    "room_map_button_enabled",
    "room_map_caption_enabled",
}


class RemoteConfigValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RemoteConfigContext:
    group_id: Optional[int]
    group_course: Optional[int]
    group_faculty_id: Optional[int]
    platform: Optional[str]
    app_version: Optional[str]
    now_msk: datetime

    @property
    def attributes(self) -> Dict[str, Any]:
        return {
            "group.id": self.group_id,
            "group.course": self.group_course,
            "group.faculty_id": self.group_faculty_id,
            "request.weekday_msk": self.now_msk.isoweekday(),
            "request.time_msk": self.now_msk.strftime("%H:%M"),
            "client.platform": self.platform,
            "client.version": self.app_version,
        }


@dataclass(frozen=True)
class RemoteConfigEvaluation:
    payload: Dict[str, Any]
    matched_rules: Dict[str, Optional[str]]
    refresh_interval_seconds: int


def build_remote_config_context(
    session,
    group_id: Optional[int] = None,
    platform: Optional[str] = None,
    app_version: Optional[str] = None,
    now: Optional[datetime] = None,
) -> RemoteConfigContext:
    group = None
    if group_id is not None:
        group = session.query(Group).filter(Group.id == group_id).one_or_none()

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=MOSCOW_TIMEZONE)
    current_msk = current.astimezone(MOSCOW_TIMEZONE)

    return RemoteConfigContext(
        group_id=group.id if group is not None else None,
        group_course=group.course if group is not None else None,
        group_faculty_id=group.faculty_id if group is not None else None,
        platform=platform,
        app_version=app_version,
        now_msk=current_msk,
    )


def validate_remote_config_document(document: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(document, dict):
        raise RemoteConfigValidationError("document must be a JSON object")

    serialized = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise RemoteConfigValidationError("document exceeds 128 KiB")

    _require_keys(
        document,
        required={"schema_version", "refresh_interval_seconds", "parameters"},
        optional=set(),
        path="document",
    )
    if document["schema_version"] != 1:
        raise RemoteConfigValidationError("schema_version must be 1")

    refresh_interval = document["refresh_interval_seconds"]
    if (
        not isinstance(refresh_interval, int)
        or isinstance(refresh_interval, bool)
        or not MIN_REFRESH_INTERVAL_SECONDS
        <= refresh_interval
        <= MAX_REFRESH_INTERVAL_SECONDS
    ):
        raise RemoteConfigValidationError(
            "refresh_interval_seconds must be between 60 and 3600"
        )

    parameters = document["parameters"]
    if not isinstance(parameters, dict):
        raise RemoteConfigValidationError("parameters must be an object")
    if len(parameters) > MAX_PARAMETERS:
        raise RemoteConfigValidationError("too many parameters")

    for parameter_key, parameter in parameters.items():
        _validate_parameter(parameter_key, parameter)

    return copy.deepcopy(document)


def evaluate_remote_config(
    document: Mapping[str, Any],
    context: RemoteConfigContext,
) -> RemoteConfigEvaluation:
    validated = validate_remote_config_document(document)
    payload = {}
    matched_rules = {}
    attributes = context.attributes

    for parameter_key, parameter in validated["parameters"].items():
        value = parameter["default"]
        matched_rule = None
        for rule in parameter["rules"]:
            if not rule.get("enabled", True):
                continue
            if all(_condition_matches(condition, attributes) for condition in rule["conditions"]):
                value = rule["value"]
                matched_rule = rule["id"]
                break
        payload[parameter_key] = value
        matched_rules[parameter_key] = matched_rule

    return RemoteConfigEvaluation(
        payload=payload,
        matched_rules=matched_rules,
        refresh_interval_seconds=validated["refresh_interval_seconds"],
    )


def _validate_parameter(parameter_key: Any, parameter: Any) -> None:
    if not isinstance(parameter_key, str) or not _PARAMETER_KEY_PATTERN.fullmatch(
        parameter_key
    ):
        raise RemoteConfigValidationError(
            "invalid parameter key: {!r}".format(parameter_key)
        )
    if parameter_key in _RESERVED_PARAMETERS:
        raise RemoteConfigValidationError(
            "{} is managed by the legacy safety flag store".format(parameter_key)
        )
    if not isinstance(parameter, dict):
        raise RemoteConfigValidationError(
            "parameters.{} must be an object".format(parameter_key)
        )
    _require_keys(
        parameter,
        required={"default", "rules"},
        optional={"description"},
        path="parameters.{}".format(parameter_key),
    )
    if "description" in parameter and not isinstance(parameter["description"], str):
        raise RemoteConfigValidationError("parameter description must be a string")
    _validate_json_value(parameter["default"], "{}.default".format(parameter_key))
    if parameter_key == "telemetry":
        _validate_telemetry(parameter["default"])

    rules = parameter["rules"]
    if not isinstance(rules, list):
        raise RemoteConfigValidationError("parameter rules must be an array")
    if len(rules) > MAX_RULES_PER_PARAMETER:
        raise RemoteConfigValidationError("too many rules for {}".format(parameter_key))

    seen_rule_ids = set()
    for index, rule in enumerate(rules):
        path = "parameters.{}.rules[{}]".format(parameter_key, index)
        _validate_rule(rule, path)
        if parameter_key == "telemetry":
            _validate_telemetry(rule["value"])
        if rule["id"] in seen_rule_ids:
            raise RemoteConfigValidationError(
                "duplicate rule id {!r} for {}".format(rule["id"], parameter_key)
            )
        seen_rule_ids.add(rule["id"])


def _validate_rule(rule: Any, path: str) -> None:
    if not isinstance(rule, dict):
        raise RemoteConfigValidationError("{} must be an object".format(path))
    _require_keys(
        rule,
        required={"id", "conditions", "value"},
        optional={"description", "enabled"},
        path=path,
    )
    rule_id = rule["id"]
    if not isinstance(rule_id, str) or not _RULE_ID_PATTERN.fullmatch(rule_id):
        raise RemoteConfigValidationError("{}.id is invalid".format(path))
    if "description" in rule and not isinstance(rule["description"], str):
        raise RemoteConfigValidationError("{}.description must be a string".format(path))
    if "enabled" in rule and not isinstance(rule["enabled"], bool):
        raise RemoteConfigValidationError("{}.enabled must be boolean".format(path))

    conditions = rule["conditions"]
    if not isinstance(conditions, list) or not conditions:
        raise RemoteConfigValidationError("{}.conditions must be a non-empty array".format(path))
    if len(conditions) > MAX_CONDITIONS_PER_RULE:
        raise RemoteConfigValidationError("{} has too many conditions".format(path))
    for index, condition in enumerate(conditions):
        _validate_condition(condition, "{}.conditions[{}]".format(path, index))
    _validate_json_value(rule["value"], "{}.value".format(path))


def _validate_condition(condition: Any, path: str) -> None:
    if not isinstance(condition, dict):
        raise RemoteConfigValidationError("{} must be an object".format(path))
    _require_keys(
        condition,
        required={"attribute", "operator", "value"},
        optional=set(),
        path=path,
    )
    attribute = condition["attribute"]
    operator = condition["operator"]
    value = condition["value"]
    if attribute not in _ALLOWED_ATTRIBUTES:
        raise RemoteConfigValidationError("{}.attribute is not allowed".format(path))

    if operator == "time_between":
        if attribute != "request.time_msk":
            raise RemoteConfigValidationError(
                "time_between is only valid for request.time_msk"
            )
        _parse_time_range(value, path)
        return

    if operator not in _SET_OPERATORS:
        raise RemoteConfigValidationError("{}.operator is not supported".format(path))

    expected_type = _ALLOWED_ATTRIBUTES[attribute]
    if operator in {"in", "not_in"}:
        if not isinstance(value, list) or not value or len(value) > 100:
            raise RemoteConfigValidationError(
                "{}.value must be a non-empty array with at most 100 items".format(path)
            )
        for item in value:
            _validate_attribute_value(item, expected_type, path)
    else:
        _validate_attribute_value(value, expected_type, path)


def _condition_matches(condition: Mapping[str, Any], attributes: Mapping[str, Any]) -> bool:
    actual = attributes.get(condition["attribute"])
    if actual is None:
        return False
    operator = condition["operator"]
    expected = condition["value"]
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected
    if operator == "time_between":
        start, end = _parse_time_range(expected, "condition")
        actual_minutes = _parse_clock(actual, "condition actual value")
        if start < end:
            return start <= actual_minutes < end
        return actual_minutes >= start or actual_minutes < end
    return False


def _parse_time_range(value: Any, path: str) -> Tuple[int, int]:
    if not isinstance(value, dict) or set(value) != {"start", "end"}:
        raise RemoteConfigValidationError(
            "{}.value must contain start and end times".format(path)
        )
    start = _parse_clock(value["start"], "{}.value.start".format(path))
    end = _parse_clock(value["end"], "{}.value.end".format(path))
    if start == end:
        raise RemoteConfigValidationError("time range start and end must differ")
    return start, end


def _parse_clock(value: Any, path: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}:\d{2}", value):
        raise RemoteConfigValidationError("{} must use HH:MM".format(path))
    hour, minute = (int(part) for part in value.split(":"))
    if hour > 23 or minute > 59:
        raise RemoteConfigValidationError("{} is not a valid clock time".format(path))
    return hour * 60 + minute


def _validate_attribute_value(value: Any, expected_type: type, path: str) -> None:
    if expected_type is int:
        valid = isinstance(value, int) and not isinstance(value, bool)
    else:
        valid = isinstance(value, expected_type)
    if not valid:
        raise RemoteConfigValidationError(
            "{}.value must contain {} values".format(path, expected_type.__name__)
        )


def _validate_json_value(value: Any, path: str) -> None:
    try:
        json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        raise RemoteConfigValidationError("{} is not JSON-compatible".format(path)) from error


def _require_keys(
    value: Mapping[str, Any],
    required: set,
    optional: set,
    path: str,
) -> None:
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise RemoteConfigValidationError(
            "{} is missing keys: {}".format(path, ", ".join(sorted(missing)))
        )
    if unknown:
        raise RemoteConfigValidationError(
            "{} has unknown keys: {}".format(path, ", ".join(sorted(unknown)))
        )


def _validate_telemetry(value):
    if not isinstance(value, dict) or value.get("mode") not in {"appmetrica", "sentry", "both", "off"}:
        raise RemoteConfigValidationError("telemetry.mode must be appmetrica, sentry, both or off")
    if set(value) - {"mode", "sentry_dsn"}:
        raise RemoteConfigValidationError("unknown telemetry property")
    dsn = value.get("sentry_dsn", "")
    if not isinstance(dsn, str):
        raise RemoteConfigValidationError("telemetry.sentry_dsn must be a string")
    if value["mode"] in {"sentry", "both"}:
        try:
            uri = urlsplit(dsn)
            valid = (uri.scheme == "https" and uri.hostname == "sentry.roadmapik.com"
                     and uri.username and uri.password is None and uri.port in (None, 443)
                     and re.fullmatch(r"/[0-9]+", uri.path) and not uri.query and not uri.fragment)
        except ValueError:
            valid = False
        if not valid:
            raise RemoteConfigValidationError("telemetry.sentry_dsn must target the trusted HTTPS collector")
