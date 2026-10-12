import argparse
import json
from datetime import datetime
from pathlib import Path

from core.repositories.remote_config_repository import RemoteConfigRepository
from core.services.remote_config_service import (
    MOSCOW_TIMEZONE,
    REMOTE_CONFIG_KEY,
    build_remote_config_context,
    evaluate_remote_config,
    validate_remote_config_document,
)
from db import Session


def _load_document(path: str) -> dict:
    source = Path(path)
    if source.stat().st_size > 131072:
        raise ValueError("config document exceeds 128 KiB")
    with source.open("r", encoding="utf-8") as file:
        value = json.load(file)
    return validate_remote_config_document(value)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=MOSCOW_TIMEZONE)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, inspect, publish, evaluate, or roll back remote config.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("show", help="show the current document")

    validate_parser = subparsers.add_parser("validate", help="validate a JSON file")
    validate_parser.add_argument("file")

    set_parser = subparsers.add_parser("set", help="publish a validated JSON file")
    set_parser.add_argument("file")

    history_parser = subparsers.add_parser("history", help="show retained revisions")
    history_parser.add_argument("--limit", type=int, default=20)

    rollback_parser = subparsers.add_parser(
        "rollback",
        help="publish an earlier document as a new revision",
    )
    rollback_parser.add_argument("revision", type=int)

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="evaluate the stored document or a candidate file",
    )
    evaluate_parser.add_argument("--file")
    evaluate_parser.add_argument("--group-id", type=int)
    evaluate_parser.add_argument("--platform")
    evaluate_parser.add_argument("--app-version")
    evaluate_parser.add_argument(
        "--at",
        type=_parse_datetime,
        help="ISO time; a timezone-less value is interpreted as Europe/Moscow",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "validate":
        _load_document(args.file)
        print("valid")
        return

    session = Session()
    try:
        repository = RemoteConfigRepository(session)
        if args.command == "set":
            current = repository.set(REMOTE_CONFIG_KEY, _load_document(args.file))
            print(
                "{} revision={} updated_at={}".format(
                    current.key,
                    current.revision,
                    current.updated_at.isoformat(),
                )
            )
            return

        if args.command == "show":
            current = repository.get(REMOTE_CONFIG_KEY)
            if current is None:
                raise ValueError("remote config is not initialized")
            print(
                json.dumps(
                    {
                        "key": current.key,
                        "revision": current.revision,
                        "updated_at": current.updated_at.isoformat(),
                        "document": current.document,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return

        if args.command == "history":
            if args.limit < 1 or args.limit > 100:
                raise ValueError("history limit must be between 1 and 100")
            for revision in repository.history(REMOTE_CONFIG_KEY, args.limit):
                print(
                    "revision={} created_at={}".format(
                        revision.revision,
                        revision.created_at.isoformat(),
                    )
                )
            return

        if args.command == "rollback":
            current = repository.rollback(REMOTE_CONFIG_KEY, args.revision)
            print(
                "{} revision={} restored_from={}".format(
                    current.key,
                    current.revision,
                    args.revision,
                )
            )
            return

        current = repository.get(REMOTE_CONFIG_KEY)
        if args.file:
            document = _load_document(args.file)
            source = args.file
        elif current is not None:
            document = current.document
            source = "stored revision {}".format(current.revision)
        else:
            raise ValueError("remote config is not initialized")

        context = build_remote_config_context(
            session,
            group_id=args.group_id,
            platform=args.platform,
            app_version=args.app_version,
            now=args.at,
        )
        evaluation = evaluate_remote_config(document, context)
        print(
            json.dumps(
                {
                    "source": source,
                    "context": context.attributes,
                    "payload": evaluation.payload,
                    "matched_rules": evaluation.matched_rules,
                    "refresh_interval_seconds": evaluation.refresh_interval_seconds,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
