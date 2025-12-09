#!/usr/bin/env python3
"""
Build a consolidated master workbook with one read-only sheet per term (GTA Eligible).

Input: data/processed/gta_eligible_term_<term>.json and data/processed/gta_compatibility_term_<term>.csv
Output: data/exports/Master_All_Terms.xlsx with sheets named <term> (reverse-chronological)
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
from typing import List

import openpyxl

TEMPLATE_HEADERS = [
    "Term",
    "CRN",
    "Course",
    "Sec",
    "Title",
    "Course Type",
    "Meeting Dates",
    "Time",
    "Days",
    "Hrs",
    "Room",
    "Instructor",
    "Seat",
    "Enr",
    "Crosslisted Enr",
    "Total Enr",
    "Prefer TA 1",
    "Prefer TA 2",
    "Prefer TA 3",
    "In Class",
    "Office Hours",
    "Grading",
    "Time commitment",
    "Notes",
]


def load_gta_json(term: str, base_dir: pathlib.Path) -> List[dict]:
    path = base_dir / f"gta_eligible_term_{term}.json"
    return json.loads(path.read_text())


def build_master(terms: List[str], processed_dir: pathlib.Path, export_path: pathlib.Path) -> None:
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    for term in sorted(terms, reverse=True):
        rows = load_gta_json(term, processed_dir)
        ws = wb.create_sheet(term)
        ws.append(TEMPLATE_HEADERS)
        for r in rows:
            ws.append(
                [
                    term,
                    r.get("crn", ""),
                    r.get("course", ""),
                    r.get("section", ""),
                    r.get("title", ""),
                    r.get("course_type", ""),
                    r.get("meeting_dates", ""),
                    r.get("time", ""),
                    r.get("days", ""),
                    r.get("hours", ""),
                    r.get("room", ""),
                    r.get("instructor", ""),
                    r.get("seats", ""),
                    r.get("enrolled", ""),
                    r.get("crosslisted_enrollment", ""),
                    r.get("total_enrollment", ""),
                    "", "", "", "", "", "", "", "", "",
                ]
            )
        ws.protection.sheet = True
    export_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(export_path)
    print(f"Wrote master all-terms workbook: {export_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build master workbook with one sheet per term.")
    parser.add_argument("--processed-dir", default="data/processed", help="Processed data directory.")
    parser.add_argument("--export", default="data/exports/Master_All_Terms.xlsx", help="Output workbook path.")
    args = parser.parse_args()

    processed_dir = pathlib.Path(args.processed_dir)
    terms = sorted({p.stem.split("_")[-1] for p in processed_dir.glob("gta_eligible_term_*.json")})
    build_master(terms, processed_dir, pathlib.Path(args.export))


if __name__ == "__main__":
    main()
