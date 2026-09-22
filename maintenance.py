import logging
import os
import time
from dataclasses import asdict
from datetime import datetime, timedelta

from core.observability import configure_observability, log_event
from core.services.schedule_context_service import get_schedule_context
from parsing.group_sync import sync_groups


configure_observability("schedule-maintenance")
logger = logging.getLogger("schedule-maintenance")


def main():
    observation_interval = int(os.getenv("SCHEDULE_OBSERVATION_INTERVAL", "3600"))
    group_sync_interval = int(os.getenv("GROUP_SYNC_INTERVAL", "86400"))
    last_group_sync = None

    while True:
        observation_started = time.monotonic()
        try:
            context = get_schedule_context(force_refresh=True)
            recommended = context.get("recommended", {})
            log_event(
                logger,
                logging.INFO,
                "schedule_observation.success",
                "Schedule context observation succeeded",
                {
                    "duration_ms": round(
                        (time.monotonic() - observation_started) * 1000, 2
                    ),
                    "academic_year_start": recommended.get(
                        "academic_year_start"
                    ),
                    "week": recommended.get("week"),
                    "sentinel_agreement": context.get("sentinel_agreement"),
                    "upcoming_published": context.get(
                        "upcoming", {}
                    ).get("published"),
                },
            )
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "schedule_observation.failure",
                "Schedule context observation failed",
                {
                    "duration_ms": round(
                        (time.monotonic() - observation_started) * 1000, 2
                    ),
                    "exception_type": type(error).__name__,
                },
            )

        now = datetime.now()
        if last_group_sync is None or now - last_group_sync >= timedelta(
                seconds=group_sync_interval):
            sync_started = time.monotonic()
            try:
                result = sync_groups()
                last_group_sync = now
                log_event(
                    logger,
                    logging.INFO,
                    "group_sync.success",
                    "Group synchronization succeeded",
                    {
                        **asdict(result),
                        "duration_ms": round(
                            (time.monotonic() - sync_started) * 1000, 2
                        ),
                    },
                )
            except Exception as error:
                log_event(
                    logger,
                    logging.ERROR,
                    "group_sync.failure",
                    "Group synchronization failed",
                    {
                        "duration_ms": round(
                            (time.monotonic() - sync_started) * 1000, 2
                        ),
                        "exception_type": type(error).__name__,
                    },
                )

        time.sleep(observation_interval)


if __name__ == "__main__":
    main()
