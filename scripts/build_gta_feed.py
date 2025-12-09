#!/usr/bin/env python3
"""
Build GTA-facing feed files (CSV + Excel) per term, excluding the Prefer TA columns.

Input: data/processed/gta_eligible_term_<term>.json
Output: data/exports/gta_feed_<term>.csv and data/exports/gta_feed_<term>.xlsx
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
from typing import List

import openpyxl

FIELDS = [
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
    "In Class",
    "Office Hours",
    "Grading",
    "Time commitment",
    "Notes",
]


def load_gta_json(term: str, base_dir: pathlib.Path) -> List[dict]:
    path = base_dir / f"gta_eligible_term_{term}.json"
    return json.loads(path.read_text())


def write_csv(term: str, rows: List[dict], dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for r in rows:
            writer.writerow(
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
                    "",  # In Class
                    "",  # Office Hours
                    "",  # Grading
                    "",  # Time commitment
                    "",  # Notes
                ]
            )


def write_excel(term: str, rows: List[dict], dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "GTA Feed"
    ws.append(FIELDS)
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
                "",  # In Class
                "",  # Office Hours
                "",  # Grading
                "",  # Time commitment
                "",  # Notes
            ]
        )
    wb.save(dest)


def build_for_term(term: str, processed_dir: pathlib.Path, export_dir: pathlib.Path) -> None:
    rows = load_gta_json(term, processed_dir)
    term_dir = export_dir / term
    term_dir.mkdir(parents=True, exist_ok=True)
    csv_path = term_dir / f"gta_feed_{term}.csv"
    xlsx_path = term_dir / f"gta_feed_{term}.xlsx"
    write_csv(term, rows, csv_path)
    write_excel(term, rows, xlsx_path)
    print(f"Wrote GTA feed for {term}: {csv_path} and {xlsx_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GTA-facing feed (no Prefer TA columns).")
    parser.add_argument("terms", nargs="+", help="Term codes, e.g., 202610 202630.")
    parser.add_argument("--processed-dir", default="data/processed", help="Directory containing processed files.")
    parser.add_argument("--export-dir", default="data/exports", help="Output directory for feed files.")
    args = parser.parse_args()

    processed_dir = pathlib.Path(args.processed_dir)
    export_dir = pathlib.Path(args.export_dir)
    for term in args.terms:
        build_for_term(term, processed_dir, export_dir)


if __name__ == "__main__":
    main()
