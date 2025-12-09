#!/usr/bin/env python3
"""
Post-process course JSON to add crosslisting metadata and totals.

Rules:
- crosslist: comma-separated CRNs of other courses that share the same term AND identical time, days, and instructor (all non-empty).
- lower-crosslist: True if this course has the lowest course number within its crosslist group (or if it has no crosslist siblings).
- total_enrollment / total_seats: sums across a crosslisted group (otherwise the course's own values).
- conflicts: comma-separated CRNs of other courses (same term) with identical time and days, excluding itself and its crosslist siblings.

Usage:
    python scripts/process_courses.py data/course_COMP_202610.json data/course_COMP_202630.json --outdir data/processed --combine data/processed/course_all_processed.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, List


def _to_int(value: str) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _course_number(row: Dict) -> int | None:
    course = row.get("course", "")
    m = re.search(r"(\d{3,})", course)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def _parse_time_range(time_str: str) -> tuple[int, int] | None:
    """Parse times like '10:00AM-11:50AM' into minutes since midnight."""
    if not time_str:
        return None
    m = re.match(r"\s*(\d{1,2}):(\d{2})(AM|PM)\s*-\s*(\d{1,2}):(\d{2})(AM|PM)\s*", time_str, re.IGNORECASE)
    if not m:
        return None
    h1, m1, ap1, h2, m2, ap2 = m.groups()
    def to_minutes(h, mi, ap):
        h = int(h) % 12
        if ap.upper() == "PM":
            h += 12
        return h * 60 + int(mi)
    start = to_minutes(h1, m1, ap1)
    end = to_minutes(h2, m2, ap2)
    return (start, end) if end > start else None


def _parse_days(days_str: str) -> List[str]:
    if not days_str:
        return []
    # Split on commas or whitespace, keep original order
    tokens = [t.upper() for t in re.split(r"[,\s]+", days_str.strip()) if t]
    return tokens


def _times_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def _parse_date_range(date_str: str) -> tuple[str, str] | None:
    if not date_str:
        return None
    m = re.match(r"\s*(\d{2}-[A-Za-z]{3}-\d{4})\s+to\s+(\d{2}-[A-Za-z]{3}-\d{4})\s*", date_str)
    if not m:
        return None
    from datetime import datetime

    try:
        start_dt = datetime.strptime(m.group(1).upper(), "%d-%b-%Y")
        end_dt = datetime.strptime(m.group(2).upper(), "%d-%b-%Y")
        return start_dt.date().isoformat(), end_dt.date().isoformat()
    except Exception:
        return None


def process_rows(rows: List[Dict]) -> List[Dict]:
    # Normalize times, days, dates for each row (nested under "normalized")
    for row in rows:
        trange = _parse_time_range(row.get("time", ""))
        days_list = _parse_days(row.get("days", ""))
        drange = _parse_date_range(row.get("meeting_dates", ""))
        normalized = {
            "time": {
                "start_24": f"{trange[0]//60:02d}:{trange[0]%60:02d}" if trange else "",
                "end_24": f"{trange[1]//60:02d}:{trange[1]%60:02d}" if trange else "",
                "start_minutes": trange[0] if trange else None,
                "end_minutes": trange[1] if trange else None,
            },
            "days": {
                "list": days_list,
                "canonical": "".join(days_list),
            },
            "dates": {
                "start": drange[0] if drange else "",
                "end": drange[1] if drange else "",
            },
        }
        row["normalized"] = normalized

    # Group by (term, time, days, instructor) within the same term for crosslisting
    xlist_groups = {}
    # Group by (term, time, days) for conflicts (independent of instructor)
    conflict_groups = {}
    for idx, row in enumerate(rows):
        term = row.get("term", "").strip()
        time = row.get("time", "").strip()
        days = row.get("days", "").strip()
        instructor = row.get("instructor", "").strip()
        # Only consider rows with all three present for crosslisting
        if term and time and days and instructor:
            key = (term, time, days, instructor)
            xlist_groups.setdefault(key, []).append(idx)
        if term and time and days:
            ckey = (term, time, days)
            conflict_groups.setdefault(ckey, []).append(idx)

    for key, indices in xlist_groups.items():
        if len(indices) < 2:
            continue
        # Compute totals across the group
        total_seats = 0
        total_enrolled = 0
        crns_in_group = []
        course_numbers = []
        for i in indices:
            row = rows[i]
            crn = row.get("crn", "").strip()
            if crn:
                crns_in_group.append(crn)
            total_seats += _to_int(row.get("seats", "0"))
            total_enrolled += _to_int(row.get("enrolled", "0"))
            course_numbers.append(_course_number(row))

        # Determine lowest course number (if any parsed)
        parsed_numbers = [n for n in course_numbers if n is not None]
        min_number = min(parsed_numbers) if parsed_numbers else None

        for i in indices:
            row = rows[i]
            crn = row.get("crn", "").strip()
            # Crosslist is all other CRNs in the group
            others = [c for c in crns_in_group if c != crn]
            row["crosslist"] = ",".join(sorted(others)) if others else ""
            # Lower-crosslist: true if this is the lowest-numbered course in the group (or if no numbers parsed, fallback to True)
            num = _course_number(row)
            row["lower-crosslist"] = True if (min_number is None or (num is not None and num == min_number)) else False
            row["total_seats"] = total_seats if total_seats else _to_int(row.get("seats", "0"))
            row["total_enrollment"] = total_enrolled if total_enrolled else _to_int(row.get("enrolled", "0"))

    # For rows not in multi-member groups, ensure defaults
    for row in rows:
        row.setdefault("crosslist", "")
        # No crosslist siblings -> lowest by definition
        row.setdefault("lower-crosslist", True)
        row.setdefault("total_seats", _to_int(row.get("seats", "0")))
        row.setdefault("total_enrollment", _to_int(row.get("enrolled", "0")))
        row.setdefault("conflicts", "")

    # Compute conflicts (same term, overlapping time ranges with overlapping days), excluding self and crosslist siblings
    term_records: Dict[str, List[Dict]] = {}
    for r in rows:
        term = r.get("term", "").strip()
        term_records.setdefault(term, []).append(r)

    for term, term_rows in term_records.items():
        parsed = []
    for r in term_rows:
        trange = _parse_time_range(r.get("time", ""))
        days = _parse_days(r.get("days", ""))
        parsed.append((r, trange, set(days)))
        conflict_sets = {id(r): set() for r, _, _ in parsed}
        n = len(parsed)
        for i in range(n):
            r1, t1, d1 = parsed[i]
            if not t1 or not d1:
                continue
            crn1 = r1.get("crn", "").strip()
            sib1 = set(r1.get("crosslist", "").split(",")) if r1.get("crosslist") else set()
            for j in range(i + 1, n):
                r2, t2, d2 = parsed[j]
                if not t2 or not d2:
                    continue
                if not (d1 & d2):
                    continue
                if not _times_overlap(t1, t2):
                    continue
                crn2 = r2.get("crn", "").strip()
                sib2 = set(r2.get("crosslist", "").split(",")) if r2.get("crosslist") else set()
                # Exclude crosslist siblings
                if crn2 in sib1 or crn1 in sib2:
                    continue
                if crn1 and crn2 and crn1 != crn2:
                    conflict_sets[id(r1)].add(crn2)
                    conflict_sets[id(r2)].add(crn1)
        for r, _, _ in parsed:
            r["conflicts"] = ",".join(sorted(conflict_sets[id(r)]))

    # Ensure conflicts exists for all
    for row in rows:
        row.setdefault("conflicts", "")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-process course JSON files.")
    parser.add_argument("inputs", nargs="+", help="Input JSON files to process.")
    parser.add_argument("--outdir", default="data/processed", help="Directory for processed JSON outputs.")
    parser.add_argument("--combine", default="", help="Optional combined output JSON path.")
    args = parser.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    all_processed: List[Dict] = []
    term_buckets: Dict[str, List[Dict]] = {}
    for input_path in args.inputs:
        src = pathlib.Path(input_path)
        rows = json.loads(src.read_text())
        processed = process_rows(rows)
        dest = outdir / src.name
        dest.write_text(json.dumps(processed, indent=2))
        all_processed.extend(processed)
        # Bucket by term for term-based outputs
        for r in processed:
            term = r.get("term", "").strip()
            if term:
                term_buckets.setdefault(term, []).append(r)
        print(f"Processed {src} -> {dest} ({len(processed)} rows)")

    # Write per-term processed files
    for term, rows in term_buckets.items():
        term_path = outdir / f"term_{term}_processed.json"
        term_path.write_text(json.dumps(rows, indent=2))
        print(f"Wrote term-processed file: {term_path} ({len(rows)} rows)")

    if args.combine:
        combined_path = pathlib.Path(args.combine)
        combined_path.parent.mkdir(parents=True, exist_ok=True)
        combined_path.write_text(json.dumps(all_processed, indent=2))
        print(f"Wrote combined processed file: {combined_path} ({len(all_processed)} rows)")


if __name__ == "__main__":
    main()
