#!/usr/bin/env python3
"""
Build a nested JSON of courses -> titles -> instructors from processed course JSON.

Default input: data/processed/course_all_processed.json
Default output: data/processed/course_title_instructors.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, List


def _course_sort_key(course: str):
    m = re.match(r"([A-Za-z]+)\\s*(\\d+)", course)
    if m:
        subj = m.group(1)
        num = int(m.group(2))
        return (subj, num, course)
    return ("", 0, course)


def build_map(rows: List[Dict]) -> Dict[str, Dict[str, List[str]]]:
    agg: Dict[str, Dict[str, set]] = {}
    for r in rows:
        course = (r.get("course") or "").strip()
        title = (r.get("title") or "").strip()
        instr = (r.get("instructor") or "").strip()
        if not course or not title or not instr:
            continue
        agg.setdefault(course, {}).setdefault(title, set()).add(instr)

    out: Dict[str, Dict[str, List[str]]] = {}
    for course in sorted(agg.keys(), key=_course_sort_key):
        title_map = {}
        for title in sorted(agg[course].keys()):
            title_map[title] = sorted(agg[course][title])
        out[course] = title_map
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build course -> titles -> instructors map from processed JSON.")
    parser.add_argument("--input", default="data/processed/course_all_processed.json", help="Input processed JSON path.")
    parser.add_argument("--output", default="data/processed/course_title_instructors.json", help="Output JSON path.")
    args = parser.parse_args()

    src = pathlib.Path(args.input)
    rows = json.loads(src.read_text())
    out = build_map(rows)

    dest = pathlib.Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(f"Wrote course title map: {dest} ({len(out)} courses)")


if __name__ == "__main__":
    main()
