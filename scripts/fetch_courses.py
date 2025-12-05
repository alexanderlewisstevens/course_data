#!/usr/bin/env python3
"""
Quick scraper for the DU course offerings legacy HTML forms.

Flow:
1) GET pducrs.p_duSlctCrsOff to read term/college options.
2) POST pducrs.p_duSlctSubj with term+college to read subjects.
3) POST pducrs.p_duSrchCrsOff with p_subj to get course rows.

This is intentionally simple for demonstration and can be extended
to loop over all terms/colleges/subjects.
"""

from __future__ import annotations

import csv
import dataclasses
import pathlib
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://apps25.du.edu:8446/mdb/"
COURSE_LIST_PATH = pathlib.Path("data/sample_courses.csv")
COURSE_JSON_PATH = pathlib.Path("data/json/sample_courses.json")
TIMEOUT = 30  # seconds


@dataclasses.dataclass
class TermOption:
    value: str
    label: str


@dataclasses.dataclass
class CollegeOption:
    value: str
    label: str


@dataclasses.dataclass
class SubjectOption:
    value: str  # e.g., "COMP,202670,ALL,"
    code: str
    term: str
    college: str
    label: str


@dataclasses.dataclass
class CourseRow:
    term: str
    college: str
    subject_code: str
    subject_label: str
    crn: str
    course: str
    section: str
    title: str
    course_type: str
    meeting_dates: str
    time: str
    days: str
    hours: str
    room: str
    instructor: str
    seats: str
    enrolled: str
    exam_meeting_dates: str = ""
    exam_time: str = ""
    exam_days: str = ""
    exam_room: str = ""
    description: str = ""


def fetch_terms_and_colleges(session: requests.Session) -> tuple[list[TermOption], list[CollegeOption]]:
    resp = session.get(f"{BASE_URL}pducrs.p_duSlctCrsOff", timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    def parse_select(name: str, cls):
        sel = soup.find("select", attrs={"name": name})
        if not sel:
            raise RuntimeError(f"select {name} not found")
        opts = []
        for opt in sel.find_all("option"):
            opts.append(cls(value=opt.get("value", "").strip(), label=opt.text.strip()))
        return opts

    return parse_select("p_term", TermOption), parse_select("p_coll", CollegeOption)


def fetch_subjects(session: requests.Session, term: str, college: str) -> list[SubjectOption]:
    resp = session.post(
        f"{BASE_URL}pducrs.p_duSlctSubj",
        data={"p_term": term, "p_coll": college},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    sel = soup.find("select", attrs={"name": "p_subj"})
    if not sel:
        raise RuntimeError("subject select not found; check term/college")

    subjects: list[SubjectOption] = []
    for opt in sel.find_all("option"):
        val = opt.get("value", "")
        parts = val.split(",")
        code = parts[0] if parts else ""
        subj_term = parts[1] if len(parts) > 1 else ""
        subj_coll = parts[2] if len(parts) > 2 else ""
        subjects.append(
            SubjectOption(
                value=val,
                code=code,
                term=subj_term,
                college=subj_coll,
                label=opt.text.strip(),
            )
        )
    return subjects


def fetch_courses(
    session: requests.Session,
    subject: SubjectOption,
    college_label: str | None = None,
    term_label: str | None = None,
) -> list[CourseRow]:
    resp = session.post(
        f"{BASE_URL}pducrs.p_duSrchCrsOff",
        data={"p_subj": subject.value},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows: list[CourseRow] = []
    last_course: Optional[CourseRow] = None
    exam_eligible_types = {"lecture", "lecture/lab", "online/distance"}

    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) != 13:
            continue
        texts = [td.get_text(strip=True) for td in tds]
        # Skip spacer rows that have mostly blanks
        non_empty = [t for t in texts if t]
        if len(non_empty) <= 3:
            continue
        # Rows without a CRN are final exam/extra meeting rows; attach to previous course.
        if not texts[0] and last_course:
            if last_course.course_type.strip().lower() in exam_eligible_types and not last_course.exam_meeting_dates:
                last_course.exam_meeting_dates = texts[5]
                last_course.exam_time = texts[6]
                last_course.exam_days = texts[7]
                last_course.exam_room = texts[9]
                continue
            if last_course.course_type.strip().lower() in exam_eligible_types and not last_course.description:
                desc_parts = [texts[3], texts[4], texts[5], texts[6], texts[7], texts[9]]
                last_course.description = " | ".join([p for p in desc_parts if p])
            continue
        rows.append(
            CourseRow(
                term=subject.term or term_label or "",
                college=subject.college or college_label or "",
                subject_code=subject.code,
                subject_label=subject.label,
                crn=texts[0],
                course=texts[1],
                section=texts[2],
                title=texts[3],
                course_type=texts[4],
                meeting_dates=texts[5],
                time=texts[6],
                days=texts[7],
                hours=texts[8],
                room=texts[9],
                instructor=texts[10],
                seats=texts[11],
                enrolled=texts[12],
            )
        )
        last_course = rows[-1]
    return rows


def write_courses_csv(rows: list[CourseRow], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in dataclasses.fields(CourseRow)])
        for row in rows:
            writer.writerow(dataclasses.astuple(row))


def write_courses_json(rows: list[CourseRow], path: pathlib.Path) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump([dataclasses.asdict(r) for r in rows], f, indent=2)


def demo(
    term_value: str = "202670",
    college_value: str = "ALL",
    subject_code: str = "COMP",
    output_path: pathlib.Path = COURSE_LIST_PATH,
) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": "du-course-scraper/0.1"})

    subjects = fetch_subjects(session, term_value, college_value)
    match: Optional[SubjectOption] = None
    for subj in subjects:
        if subj.code.upper() == subject_code.upper():
            match = subj
            break

    if not match:
        raise SystemExit(f"Subject {subject_code} not found for term {term_value} + college {college_value}")

    courses = fetch_courses(session, match)
    write_courses_csv(courses, output_path)
    json_path = output_path.with_suffix(".json") if output_path.suffix else COURSE_JSON_PATH
    write_courses_json(courses, json_path)

    # Print a quick preview
    print(f"Term: {term_value} | College: {college_value} | Subject: {match.code} ({match.label})")
    print(f"Found {len(courses)} course rows; saved to {output_path} and {json_path}")
    for course in courses[:5]:
        print(f"- {course.course} {course.section}: {course.title} [{course.time} {course.days}] by {course.instructor}")


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "202670"  # Autumn Quarter 2026
    college = sys.argv[2] if len(sys.argv) > 2 else "ALL"  # All Colleges
    subject = sys.argv[3] if len(sys.argv) > 3 else "COMP"  # Computer Science
    out_path = pathlib.Path(sys.argv[4]) if len(sys.argv) > 4 else COURSE_LIST_PATH
    demo(term, college, subject, out_path)
