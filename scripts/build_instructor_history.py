#!/usr/bin/env python3
"""
Aggregate instructor preference history from a folder of Excel files.

Structure:
- Input directory (default: data/history/excel) containing .xlsx/.xlsm files.
- Output JSON (default: data/history/instructor_history.json) keyed as:
    { term: { course: { instructor: [ {section, office_hours, in_class, grading, notes, source_*}, ... ] } } }
  Entries are sorted by source modified time, then file/sheet/section for stability.

Expected headers (case-insensitive, synonyms allowed):
- term, course, section, instructor, office hours, in class, grading, notes
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import datetime
from typing import Dict, List, Tuple

import openpyxl

HEADER_ALIASES = {
    "term": {"term", "quarter", "semester", "term code", "term_code", "termcode"},
    "course": {"course", "course number", "course_number", "course num", "course_num", "course id", "courseid"},
    "section": {"section", "sec"},
    "instructor": {"instructor", "instructor name", "professor", "faculty", "instructor_name"},
    "listed_instructor": {"listed instructor", "listed_instructor"},
    "updated_instructor": {"updated instructor", "updated_instructor"},
    "office_hours": {"office hours", "office_hours", "officehrs", "officehours"},
    "in_class": {"in class", "in-class", "inclass"},
    "grading": {"grading", "grades", "grade"},
    "time_commitment": {"time commitment", "time_commitment", "timecommitment", "time committment"},
    "notes": {"notes", "note", "comments", "comment", "other notes", "other_notes", "course notes", "course_notes"},
    "crn": {"crn"},
    "title": {"title", "course title", "course_title"},
}


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    s = str(value).strip().lower()
    return s in {"y", "yes", "true", "t", "1", "x", "✓", "check", "checked"}


def _normalize_str(value) -> str:
    return str(value).strip() if value is not None else ""


def _match_headers(headers: List[str]) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for idx, raw in enumerate(headers):
        if raw is None:
            continue
        name = str(raw).strip().lower()
        for canonical, aliases in HEADER_ALIASES.items():
            if name == canonical or name in aliases:
                mapping.setdefault(canonical, idx)
                break
    return mapping


def _infer_term(path: pathlib.Path, row, mapping) -> str:
    # Prefer explicit column if present
    if "term" in mapping:
        return _normalize_str(row[mapping["term"]])
    # Fallback: derive from filename e.g., "Faculty GTA Survey Fall 2025.xlsx"
    name = path.stem
    m = re.search(r"(winter|spring|summer|fall)[ _-]*(20\d{2})", name, re.IGNORECASE)
    if m:
        season = m.group(1).title()
        year = m.group(2)
        return f"{season} {year}"
    return "unknown"


def _sort_key(term: str, course: str, instructor: str, entry: Dict) -> Tuple:
    ts = entry.get("_sort_ts") or ""
    try:
        ts_dt = datetime.fromisoformat(ts)
    except Exception:
        ts_dt = datetime.min
    return (term, course, instructor, ts_dt, entry.get("source_file", ""), entry.get("source_sheet", ""), entry.get("section", ""))


def extract_history(input_dir: pathlib.Path) -> Dict[str, Dict[str, Dict[str, List[Dict]]]]:
    history: Dict[str, Dict[str, Dict[str, List[Dict]]]] = {}
    files = sorted(
        [p for p in input_dir.glob("**/*") if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm"}]
    )
    for path in files:
        try:
            wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        except Exception as exc:
            print(f"Skipping {path} (unable to open): {exc}")
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue
            header = rows[0]
            mapping = _match_headers([h if h is not None else "" for h in header])
            has_instructor = any(k in mapping for k in ("instructor", "listed_instructor", "updated_instructor"))
            if "course" not in mapping or not has_instructor:
                continue
            for idx, row in enumerate(rows[1:], start=2):
                course = _normalize_str(row[mapping["course"]])
                instructor = ""
                listed_instructor = ""
                updated_instructor = ""
                if "updated_instructor" in mapping:
                    updated_instructor = _normalize_str(row[mapping["updated_instructor"]])
                if "listed_instructor" in mapping:
                    listed_instructor = _normalize_str(row[mapping["listed_instructor"]])
                if updated_instructor:
                    instructor = updated_instructor
                elif listed_instructor:
                    instructor = listed_instructor
                if not instructor and "instructor" in mapping:
                    instructor = _normalize_str(row[mapping["instructor"]])
                if not course or not instructor:
                    continue
                term = _infer_term(path, row, mapping)
                section = _normalize_str(row[mapping["section"]]) if "section" in mapping else ""
                office_hours = _parse_bool(row[mapping["office_hours"]]) if "office_hours" in mapping else False
                in_class = _parse_bool(row[mapping["in_class"]]) if "in_class" in mapping else False
                grading = _parse_bool(row[mapping["grading"]]) if "grading" in mapping else False
                time_commitment = _normalize_str(row[mapping["time_commitment"]]) if "time_commitment" in mapping else ""
                notes = _normalize_str(row[mapping["notes"]]) if "notes" in mapping else ""
                crn = _normalize_str(row[mapping["crn"]]) if "crn" in mapping else ""
                title = _normalize_str(row[mapping["title"]]) if "title" in mapping else ""

                entry = {
                    "section": section,
                    "office_hours": office_hours,
                    "in_class": in_class,
                    "grading": grading,
                    "time_commitment": time_commitment,
                    "notes": notes,
                    "crn": crn,
                    "title": title,
                    "instructor": instructor,
                    "listed_instructor": listed_instructor,
                    "updated_instructor": updated_instructor,
                    "source_file": str(path.name),
                    "source_row": idx,
                    "_sort_ts": mtime,
                }

                term_key = term or "unknown"
                history.setdefault(term_key, {}).setdefault(course, {}).setdefault(instructor, []).append(entry)

    # Sort entries for stability
    for term, courses in history.items():
        for course, instructors in courses.items():
            for instructor, entries in instructors.items():
                entries.sort(key=lambda e: _sort_key(term, course, instructor, e))
                for e in entries:
                    e.pop("_sort_ts", None)

    return history


def main() -> None:
    parser = argparse.ArgumentParser(description="Build instructor preference history JSON from Excel files.")
    parser.add_argument("--input-dir", default="data/history/excel", help="Directory containing Excel files.")
    parser.add_argument("--output", default="data/history/instructor_history.json", help="Output JSON path.")
    args = parser.parse_args()

    input_dir = pathlib.Path(args.input_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    history = extract_history(input_dir)
    output_path.write_text(json.dumps(history, indent=2))
    print(f"Wrote instructor history: {output_path} ({len(history)} term(s))")


if __name__ == "__main__":
    main()
