from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple

import requests
from bs4 import BeautifulSoup

from core.models.faculty import Faculty
from core.models.group import Group
from core.request import headers
from db import Session


BASE_URL = "https://rasp.unecon.ru"


@dataclass(frozen=True)
class FacultySnapshot:
    id: int
    name: str


@dataclass(frozen=True)
class GroupSnapshot:
    id: int
    name: str
    faculty_id: int
    course: int


@dataclass(frozen=True)
class GroupSyncResult:
    faculties: int
    groups: int
    created: int
    updated: int
    missing: int
    deactivated: int


def _get(session: requests.Session, path: str, params=None) -> BeautifulSoup:
    response = session.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        params=params,
        timeout=(5, 20),
    )
    response.raise_for_status()
    return BeautifulSoup(response.content, features="html.parser")


def scrape_group_snapshot() -> Tuple[List[FacultySnapshot], List[GroupSnapshot]]:
    request_session = requests.Session()
    request_session.headers.update(headers)

    root = _get(request_session, "raspisanie.php")
    faculties = [
        FacultySnapshot(
            id=int(link["data-fakultet_kod"]),
            name=link.get_text(" ", strip=True),
        )
        for link in root.select("div.fakultets a[data-fakultet_kod]")
    ]

    groups: List[GroupSnapshot] = []
    for faculty in faculties:
        faculty_page = _get(
            request_session,
            "raspisanie.php",
            params={"fakultet": faculty.id},
        )
        courses = sorted({
            int(link["data-kurs"])
            for link in faculty_page.select("div.kurses a[data-kurs]")
        })
        if not courses:
            raise ValueError(f"Faculty {faculty.id} has no courses")

        for course in courses:
            course_page = _get(
                request_session,
                "raspisanie.php",
                params={"fakultet": faculty.id, "kurs": course},
            )
            for link in course_page.select(
                    'div.grps a[href*="raspisanie_grp.php"]'):
                group_id = int(link["href"].split("g=")[-1].split("&")[0])
                groups.append(GroupSnapshot(
                    id=group_id,
                    name=link.get_text(" ", strip=True),
                    faculty_id=faculty.id,
                    course=course,
                ))

    _validate_snapshot(faculties, groups)
    return faculties, groups


def _validate_snapshot(
        faculties: Iterable[FacultySnapshot],
        groups: Iterable[GroupSnapshot]) -> None:
    faculties = list(faculties)
    groups = list(groups)
    if len(faculties) < 5:
        raise ValueError(f"Suspicious faculty snapshot size: {len(faculties)}")
    if len(groups) < 100:
        raise ValueError(f"Suspicious group snapshot size: {len(groups)}")

    faculty_ids = {faculty.id for faculty in faculties}
    group_ids = [group.id for group in groups]
    if len(group_ids) != len(set(group_ids)):
        raise ValueError("Group snapshot contains duplicate IDs")
    if any(group.faculty_id not in faculty_ids for group in groups):
        raise ValueError("Group snapshot references an unknown faculty")


def sync_groups(
        now: datetime = None,
        missing_grace: timedelta = timedelta(days=7),
        dry_run: bool = False) -> GroupSyncResult:
    now = now or datetime.now()
    faculty_snapshot, group_snapshot = scrape_group_snapshot()
    session = Session()
    try:
        existing_groups: Dict[int, Group] = {
            group.id: group for group in session.query(Group).all()
        }
        active_group_count = sum(
            1 for group in existing_groups.values() if group.is_active
        )
        if active_group_count:
            ratio = len(group_snapshot) / active_group_count
            if ratio < 0.5 or ratio > 1.5:
                raise ValueError(
                    f"Suspicious active group-count change: "
                    f"{active_group_count} -> "
                    f"{len(group_snapshot)}")

        for faculty in faculty_snapshot:
            model = session.query(Faculty).get(faculty.id)
            if model is None:
                session.add(Faculty(id=faculty.id, name=faculty.name))
            else:
                model.name = faculty.name

        created = 0
        updated = 0
        seen_ids = set()
        for snapshot in group_snapshot:
            seen_ids.add(snapshot.id)
            model = existing_groups.get(snapshot.id)
            if model is None:
                session.add(Group(
                    id=snapshot.id,
                    name=snapshot.name,
                    faculty_id=snapshot.faculty_id,
                    course=snapshot.course,
                    is_active=True,
                    first_seen_at=now,
                    last_seen_at=now,
                ))
                created += 1
                continue

            if (model.name, model.faculty_id, model.course, model.is_active) != (
                    snapshot.name, snapshot.faculty_id, snapshot.course, True):
                updated += 1
            model.name = snapshot.name
            model.faculty_id = snapshot.faculty_id
            model.course = snapshot.course
            model.is_active = True
            model.last_seen_at = now
            model.missing_since = None

        missing = 0
        deactivated = 0
        for group_id, model in existing_groups.items():
            if group_id in seen_ids:
                continue
            missing += 1
            if model.missing_since is None:
                model.missing_since = now
            elif model.is_active and now - model.missing_since >= missing_grace:
                model.is_active = False
                deactivated += 1

        result = GroupSyncResult(
            faculties=len(faculty_snapshot),
            groups=len(group_snapshot),
            created=created,
            updated=updated,
            missing=missing,
            deactivated=deactivated,
        )
        if dry_run:
            session.rollback()
        else:
            session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print(sync_groups())
