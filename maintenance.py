import logging
import os
import time
from datetime import datetime, timedelta

from core.services.schedule_context_service import get_schedule_context
from parsing.group_sync import sync_groups


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("schedule-maintenance")


def main():
    observation_interval = int(os.getenv("SCHEDULE_OBSERVATION_INTERVAL", "3600"))
    group_sync_interval = int(os.getenv("GROUP_SYNC_INTERVAL", "86400"))
    last_group_sync = None

    while True:
        try:
            context = get_schedule_context(force_refresh=True)
            logger.info("Schedule context: %s", context)
        except Exception:
            logger.exception("Schedule context observation failed")

        now = datetime.now()
        if last_group_sync is None or now - last_group_sync >= timedelta(
                seconds=group_sync_interval):
            try:
                result = sync_groups()
                last_group_sync = now
                logger.info("Group synchronization: %s", result)
            except Exception:
                logger.exception("Group synchronization failed")

        time.sleep(observation_interval)


if __name__ == "__main__":
    main()
