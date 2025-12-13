#!/usr/bin/env python3
"""
Build a nested JSON of course -> title -> instructor with merged preference history.

Inputs:
- Processed courses JSON (default: data/processed/course_all_processed.json)
- Instructor history JSON (default: data/history/instructor_history.json)

Output (default: data/processed/course_instructor_history.json):
{
  "<course>": {
    "<title>": {
      "<canonical_instructor>": {
        "display_name": "<first seen raw name>",
        "aliases": [...raw names...],
        "history": [
          {
            "term": "...",
            "section": "...",
            "crn": "...",
            "title": "...",
            "office_hours": bool,
            "in_class": bool,
            "grading": bool,
            "notes": "...",
            "source_file": "...",
            "source_sheet": "...",
            "source_row": int,
            "source_modified": "ISO timestamp"
          }
        ]
      }
    }
  }
}

Instructor names are grouped by a simple normalization (letters only, lowercase, tokens sorted, single-letter tokens dropped) to reduce duplicates like "Gao, Sky T." vs "Sky Gao". All raw name variants are preserved in "aliases".
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, List, Any

# Ensure sibling imports work when run as a script
import sys
CURRENT_DIR = pathlib.Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
import build_instructor_history  # type: ignore


def _normalize_name(name: str) -> str:
    tokens = re.findall(r"[A-Za-z]+", (name or "").lower())
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(sorted(tokens))


def _get_slot(store: Dict, course: str, title: str, canonical_name: str, raw_name: str, *, official: bool = False) -> Dict[str, Any]:
    course_map = store.setdefault(course, {})
    title_map = course_map.setdefault(title, {})
    entry = title_map.setdefault(
        canonical_name,
        {
            "display_name": raw_name,
            "history": [],
        },
    )
    if official or not entry.get("display_name"):
        entry["display_name"] = raw_name
    return entry


def _normalize_course_key(course: str, store: Dict) -> str:
    """If the course is just a number (e.g., '1101') and a COMP-prefixed entry exists, use that."""
    course = course.strip()
    if course and not re.search(r"[A-Za-z]", course):
        prefixed = f"COMP {course}"
        if prefixed in store:
            return prefixed
    return course


def merge_processed_rows(store: Dict, rows: List[Dict]) -> None:
    for r in rows:
        course = (r.get("course") or "").strip()
        title = (r.get("title") or "").strip() or "Unknown Title"
        instr = (r.get("instructor") or "").strip()
        if not course or not instr:
            continue
        canonical = _normalize_name(instr)
        slot = _get_slot(store, course, title, canonical, instr, official=True)
        # no history added here; ensures presence in map


def merge_history(store: Dict, history: Dict) -> None:
    for term, courses in history.items():
        for course, instructors in courses.items():
            course_key = _normalize_course_key(course, store)
            for instr_raw, entries in instructors.items():
                canonical = _normalize_name(instr_raw)
                for e in entries:
                    title = (e.get("title") or "").strip() or "Unknown Title"
                    slot = _get_slot(store, course_key, title, canonical, instr_raw, official=False)
                    record = {
                        "term": term,
                        "section": e.get("section", ""),
                        "crn": e.get("crn", ""),
                        "office_hours": bool(e.get("office_hours", False)),
                        "in_class": bool(e.get("in_class", False)),
                        "grading": bool(e.get("grading", False)),
                        "time_commitment": e.get("time_commitment", ""),
                    }
                    record["notes"] = (e.get("notes") or "").strip()
                    slot["history"].append(record)


def finalize(store: Dict) -> Dict:
    out: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}
    for course in sorted(store.keys()):
        out[course] = {}
        for title in sorted(store[course].keys()):
            out[course][title] = {}
            for canon in sorted(store[course][title].keys()):
                entry = store[course][title][canon]
                display = entry["display_name"]
                out[course][title][canon] = {
                    "display_name": display,
                    "history": entry["history"],
                }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build course/title/instructor map with preference history.")
    parser.add_argument("--courses", default="data/processed/course_all_processed.json", help="Processed courses JSON.")
    parser.add_argument("--history", default="data/history/instructor_history.json", help="Instructor history JSON (will be generated from --history-dir if missing).")
    parser.add_argument("--history-dir", default="data/history/excel", help="Directory containing instructor history Excel files.")
    parser.add_argument("--output", default="data/processed/course_instructor_history.json", help="Output JSON path.")
    args = parser.parse_args()

    courses_path = pathlib.Path(args.courses)
    history_path = pathlib.Path(args.history)
    history_dir = pathlib.Path(args.history_dir)
    output_path = pathlib.Path(args.output)

    store: Dict = {}
    course_rows = json.loads(courses_path.read_text())
    merge_processed_rows(store, course_rows)

    history_data = {}
    if history_path.exists():
        history_data = json.loads(history_path.read_text())
    elif history_dir.exists():
        history_data = build_instructor_history.extract_history(history_dir)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(json.dumps(history_data, indent=2))
        print(f"Built history from Excel and wrote: {history_path}")
    else:
        print(f"History file not found: {history_path} and history dir missing: {history_dir}. Proceeding without history.")

    if history_data:
        merge_history(store, history_data)

    output = finalize(store)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote course/instructor history: {output_path} ({len(output)} courses)")


if __name__ == "__main__":
    main()
