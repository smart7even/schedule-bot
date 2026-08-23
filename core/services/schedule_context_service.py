from collections import Counter
from datetime import date, datetime
from threading import Lock
from time import monotonic
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from core.repositories.group_repository import GroupRepository
from core.request import unecon_request
from core.schedule.site_parser import SchedulePeriod, UneconParser
from core.utils.academic_year import AcademicWeek, academic_week_for
from db import Session


class ScheduleSourceError(RuntimeError):
    pass


_cache_lock = Lock()
_cached_context: Optional[Dict] = None
_cached_at = 0.0
CACHE_TTL_SECONDS = 300


def _parse_group_page(group_id: int, week: Optional[int] = None) -> Tuple[int, SchedulePeriod]:
    response = unecon_request(group_id=group_id, week=week)
    path = urlparse(response.url).path
    if response.status_code != 200 or not path.endswith("/raspisanie_grp.php"):
        raise ScheduleSourceError(
            f"UNECON group {group_id} did not return a schedule page")

    parser = UneconParser(response.content)
    try:
        return parser.get_current_week_number(), parser.get_schedule_period()
    except ValueError as error:
        raise ScheduleSourceError(str(error)) from error


def _week_dict(week: int, period: SchedulePeriod) -> Dict:
    return {
        "academic_year_start": period.academic_year_start,
        "week": week,
        "period_start": period.start.isoformat(),
        "period_end": period.end.isoformat(),
    }


def _sentinel_group_ids(limit: int = 3):
    session = Session()
    try:
        groups = GroupRepository(session).get_all()
        preferred = [
            group for group in groups
            if group.course in (1, 2, 3) and not group.name.startswith("[выпуск")
        ]
        return [group.id for group in (preferred or groups)[:limit]]
    finally:
        session.close()


def detect_schedule_context(today: date = None) -> Dict:
    today = today or datetime.now().date()
    sentinels = _sentinel_group_ids()
    if not sentinels:
        raise ScheduleSourceError("No active groups are available for rollover detection")

    observations = []
    for group_id in sentinels:
        try:
            week, first_period = _parse_group_page(group_id, week=1)
            if week != 1:
                continue
            observations.append((group_id, first_period))
        except ScheduleSourceError:
            continue

    if not observations:
        raise ScheduleSourceError("No sentinel returned a valid first-week page")

    period_counts = Counter((item[1].start, item[1].end) for item in observations)
    period_key, agreement = period_counts.most_common(1)[0]
    required_agreement = min(2, len(sentinels))
    if agreement < required_agreement:
        raise ScheduleSourceError("Sentinel groups disagree about the first week")

    first_period = SchedulePeriod(start=period_key[0], end=period_key[1])
    selected_group_id = next(
        group_id for group_id, period in observations
        if (period.start, period.end) == period_key
    )
    current_week, current_period = _parse_group_page(selected_group_id)
    calendar_current: AcademicWeek = academic_week_for(today)
    upcoming_published = (
        first_period.academic_year_start > calendar_current.academic_year_start
    )

    first_week = _week_dict(1, first_period)
    current = _week_dict(current_week, current_period)
    recommended = first_week if upcoming_published else current
    return {
        "source_academic_year_start": first_period.academic_year_start,
        "observed_at": datetime.now().isoformat(),
        "sentinel_agreement": agreement,
        "calendar_current": {
            "academic_year_start": calendar_current.academic_year_start,
            "week": calendar_current.week,
            "period_start": calendar_current.period_start.isoformat(),
            "period_end": calendar_current.period_end.isoformat(),
        },
        "source_current": current,
        "upcoming": {
            **first_week,
            "published": upcoming_published,
        },
        "recommended": recommended,
    }


def get_schedule_context(today: date = None, force_refresh: bool = False) -> Dict:
    global _cached_at, _cached_context
    if today is not None:
        return detect_schedule_context(today)

    with _cache_lock:
        if (not force_refresh and _cached_context is not None
                and monotonic() - _cached_at < CACHE_TTL_SECONDS):
            return _cached_context
        _cached_context = detect_schedule_context()
        _cached_at = monotonic()
        return _cached_context
