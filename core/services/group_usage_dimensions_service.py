import re
import threading
import time
from collections import OrderedDict
from typing import Callable, Dict, Optional, Tuple

from core.repositories.group_repository import GroupRepository
from db import Session


_GROUP_NAME_LIMIT = 64
_SAFE_SPACE = re.compile(r"\s+")


class GroupUsageDimensionsCache:
    """Resolve public group metadata for structured request logs.

    The cache keeps analytics enrichment off the critical database path for
    almost all requests. Resolution is deliberately fail-open: missing or
    unavailable metadata produces no extra dimensions and never changes the
    API response.
    """

    def __init__(
        self,
        session_factory: Callable[[], object] = Session,
        repository_factory: Callable[[object], object] = GroupRepository,
        ttl_seconds: float = 3600,
        max_entries: int = 1024,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._session_factory = session_factory
        self._repository_factory = repository_factory
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock
        self._entries: OrderedDict[
            int, Tuple[float, Dict[str, object]]
        ] = OrderedDict()
        self._lock = threading.Lock()

    def resolve(self, group_id: object) -> Dict[str, object]:
        try:
            normalized_group_id = int(group_id)
        except (TypeError, ValueError):
            return {}

        now = self._clock()
        with self._lock:
            cached = self._entries.get(normalized_group_id)
            if cached is not None and cached[0] > now:
                self._entries.move_to_end(normalized_group_id)
                return dict(cached[1])
            if cached is not None:
                del self._entries[normalized_group_id]

        dimensions = self._load(normalized_group_id)
        with self._lock:
            self._entries[normalized_group_id] = (
                now + self._ttl_seconds,
                dimensions,
            )
            self._entries.move_to_end(normalized_group_id)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
        return dict(dimensions)

    def _load(self, group_id: int) -> Dict[str, object]:
        session: Optional[object] = None
        try:
            session = self._session_factory()
            group = self._repository_factory(session).get_group_by_id(group_id)
            if group is None:
                return {}

            dimensions: Dict[str, object] = {}
            name = _normalize_group_name(getattr(group, "name", None))
            course = _positive_int(getattr(group, "course", None))
            faculty_id = _positive_int(getattr(group, "faculty_id", None))
            if name is not None:
                dimensions["group_name"] = name
            if course is not None:
                dimensions["group_course"] = course
            if faculty_id is not None:
                dimensions["group_faculty_id"] = faculty_id
            return dimensions
        except Exception:
            return {}
        finally:
            if session is not None:
                close = getattr(session, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass


def _normalize_group_name(value: object) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = _SAFE_SPACE.sub(" ", value).strip()
    if not normalized:
        return None
    return normalized[:_GROUP_NAME_LIMIT]


def _positive_int(value: object) -> Optional[int]:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return None
    return normalized if normalized > 0 else None
