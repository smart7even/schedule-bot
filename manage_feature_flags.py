import argparse

from core.repositories.feature_flag_repository import (
    FeatureFlagRepository,
    KNOWN_FEATURE_FLAGS,
)
from db import Session


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "on", "1", "yes"}:
        return True
    if normalized in {"false", "off", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false or on/off")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or update runtime feature flags.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="show current values")

    set_parser = subparsers.add_parser("set", help="change one flag")
    set_parser.add_argument("name", choices=sorted(KNOWN_FEATURE_FLAGS))
    set_parser.add_argument("enabled", type=parse_bool)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    session = Session()
    try:
        repository = FeatureFlagRepository(session)
        if args.command == "set":
            flag = repository.set(args.name, args.enabled)
            print(
                "{}={} updated_at={}".format(
                    flag.name,
                    str(bool(flag.enabled)).lower(),
                    flag.updated_at.isoformat(),
                )
            )
            return

        for name, enabled in sorted(repository.get_all().items()):
            print("{}={}".format(name, str(enabled).lower()))
    finally:
        session.close()


if __name__ == "__main__":
    main()
