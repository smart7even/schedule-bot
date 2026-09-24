"""Audit a reproducible cross-section of live university group schedules.

Run from the repository root. This deliberately extracts room data independently
of UneconParser, so a parser regression cannot validate itself.
"""

import argparse
import random
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.request import headers as university_headers  # noqa: E402
from core.schedule.site_parser import UneconParser  # noqa: E402


SOURCE_URL = "https://rasp.unecon.ru/raspisanie_grp.php"
API_BASE = "https://roadmapik.com:5000"


def normalized(value):
    return re.sub(r"\s+", " ", value or "").strip()


def choose_groups(groups, count, seed, excluded):
    """Cover faculties and courses first, then fill remaining slots at random."""
    candidates = [
        group for group in groups
        if group.get("is_active") and group.get("id") not in excluded
    ]
    random.Random(seed).shuffle(candidates)
    selected = []
    used = set(excluded)

    for key in ("faculty_id", "course"):
        seen = set()
        for group in candidates:
            value = group.get(key)
            if value is None or value in seen:
                continue
            seen.add(value)
            if group["id"] not in used and len(selected) < count:
                selected.append(group)
                used.add(group["id"])

    for group in candidates:
        if len(selected) >= count:
            break
        if group["id"] not in used:
            selected.append(group)
            used.add(group["id"])
    return selected


def source_rows(html):
    soup = BeautifulSoup(html, features="html.parser")
    rows = []
    for tr in soup.select("tr"):
        if tr.select_one("span.predmet") is None:
            continue
        room_span = tr.select_one("td.no_768 span.aud")
        building_span = tr.select_one("td.no_768 span.korpus")
        note_span = tr.select_one("span.prim")
        room = " ".join(
            normalized(text)
            for text in room_span.find_all(string=True, recursive=False)
            if normalized(text)
        ) if room_span is not None else ""
        building = normalized(building_span.get_text(" ", strip=True)) \
            if building_span is not None else ""
        note = normalized(note_span.get_text(" ", strip=True)) \
            if note_span is not None else ""
        link = room_span.select_one("a[href]") if room_span is not None else None
        room_url = urljoin(SOURCE_URL, link["href"]) if link else None
        rows.append((room, building, note, room_url))
    return rows


def check_rows(rows, lessons, api_lessons=None):
    problems = []
    if len(rows) != len(lessons):
        return [f"source has {len(rows)} rows, parser returned {len(lessons)}"]
    if api_lessons is not None and len(rows) != len(api_lessons):
        return [f"source has {len(rows)} rows, API returned {len(api_lessons)}"]

    for index, ((room, building, note, room_url), lesson) in enumerate(
        zip(rows, lessons), 1
    ):
        outputs = [("parser", lesson.location, lesson.note, lesson.room_url)]
        if api_lessons is not None:
            api_lesson = api_lessons[index - 1]
            if api_lesson["name"] != lesson.name or api_lesson["start"] != \
                    lesson.get_start_date().isoformat():
                problems.append(f"row {index}: API order/content differs from source")
                continue
            outputs.append(("API", api_lesson.get("location"),
                            api_lesson.get("note"), api_lesson.get("room_url")))

        for label, location, result_note, result_url in outputs:
            visible = normalized(location)
            for part in (room, building, note):
                if part and part not in visible:
                    problems.append(f"row {index}: {label} lost {part!r}")
            if (result_note or None) != (note or None):
                problems.append(f"row {index}: {label} note differs")
            if result_url != room_url:
                problems.append(f"row {index}: {label} room link differs")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-size", type=int, default=12,
                        help="number of additional groups to sample")
    parser.add_argument("--seed", default=date.today().isoformat(),
                        help="selection seed, printed for replay")
    parser.add_argument("--group-id", type=int, action="append", default=[],
                        help="always include a known group; repeatable")
    parser.add_argument("--check-api", action="store_true",
                        help="also compare the deployed public API")
    parser.add_argument("--api-base", default=API_BASE)
    args = parser.parse_args()
    if args.sample_size < 0:
        parser.error("--sample-size must be nonnegative")

    api = requests.Session()
    groups_response = api.get(f"{args.api_base}/group", timeout=(5, 20))
    groups_response.raise_for_status()
    groups = groups_response.json()["groups"]
    by_id = {group["id"]: group for group in groups}
    unknown = set(args.group_id) - set(by_id)
    if unknown:
        parser.error(f"unknown group IDs: {sorted(unknown)}")

    chosen = [by_id[group_id] for group_id in dict.fromkeys(args.group_id)]
    chosen += choose_groups(groups, args.sample_size, args.seed,
                            {group["id"] for group in chosen})
    print(f"seed={args.seed} groups={len(chosen)} check_api={args.check_api}")

    source = requests.Session()
    source.headers.update(university_headers)
    failures = []
    populated = 0
    for group in chosen:
        group_id = group["id"]
        try:
            response = source.get(SOURCE_URL, params={"g": group_id},
                                  timeout=(5, 20))
            response.raise_for_status()
            page = UneconParser(response.content)
            rows = source_rows(response.content)
            lessons = page.parse_page()
            week = page.get_current_week_number()
            api_lessons = None
            if args.check_api:
                api_response = api.get(
                    f"{args.api_base}/group/{group_id}/schedule",
                    params={"week": week}, timeout=(5, 20),
                )
                api_response.raise_for_status()
                api_lessons = api_response.json()["lessons"]
            problems = check_rows(rows, lessons, api_lessons)
            if lessons:
                populated += 1
            note_rooms = sum(bool(room and note) for room, _, note, _ in rows)
            print(f"{group['name']} ({group_id}): week={week} "
                  f"lessons={len(lessons)} room+note={note_rooms} "
                  f"problems={len(problems)}")
            failures.extend(f"{group['name']}: {problem}" for problem in problems)
        except (requests.RequestException, ValueError, KeyError) as error:
            failures.append(f"{group['name']}: {type(error).__name__}: {error}")

    if populated == 0:
        failures.append("no populated schedule in sample")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    print(f"audited={len(chosen)} populated={populated} failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
