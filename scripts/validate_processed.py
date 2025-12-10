#!/usr/bin/env python3
"""
Basic validation for processed course JSON outputs.

Checks:
- Crosslist symmetry: within each (term, time, days, instructor) group of size >1,
  crosslist lists all other CRNs in the group.
- Totals: total_seats / total_enrollment equal the sum of seats/enrolled in the group.
- Lower-crosslist: true only on the lowest course number in the group (or all true if no numbers parsed).
- Conflicts: for each (term, time, days) slot, conflicts list is group CRNs minus self minus crosslist siblings.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Dict, List


def _to_int(value) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _course_number(row: Dict) -> int | None:
    m = re.search(r"(\d{3,})", row.get("course", ""))
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def _parse_time_range(time_str: str) -> tuple[int, int] | None:
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


def _parse_days(days_str: str) -> set[str]:
    if not days_str:
        return set()
    tokens = re.split(r"[,\s]+", days_str.strip())
    return {t.upper() for t in tokens if t}


def _times_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def load_rows(path: pathlib.Path) -> List[Dict]:
    return json.loads(path.read_text())


def validate_crosslist(rows: List[Dict]) -> List[str]:
    errors: List[str] = []
    groups = {}
    for r in rows:
        term = r.get("term", "").strip()
        time = r.get("time", "").strip()
        days = r.get("days", "").strip()
        instr = r.get("instructor", "").strip()
        if term and time and days and instr:
            key = (term, time, days, instr)
            groups.setdefault(key, []).append(r)
    for key, group in groups.items():
        if len(group) < 2:
            continue
        crns = [g.get("crn", "").strip() for g in group if g.get("crn")]
        total_seats = sum(_to_int(g.get("seats", 0)) for g in group)
        total_enr = sum(_to_int(g.get("enrolled", 0)) for g in group)
        nums = [n for n in (_course_number(g) for g in group) if n is not None]
        min_num = min(nums) if nums else None
        for g in group:
            crn = g.get("crn", "").strip()
            expected = sorted([c for c in crns if c and c != crn])
            got = sorted([c for c in g.get("crosslist", "").split(",") if c])
            if expected != got:
                errors.append(f"crosslist mismatch for {crn} in {key}: expected {expected}, got {got}")
            if g.get("total_seats") != total_seats:
                errors.append(f"total_seats mismatch for {crn}: {g.get('total_seats')} != {total_seats}")
            if g.get("total_enrollment") != total_enr:
                errors.append(f"total_enrollment mismatch for {crn}: {g.get('total_enrollment')} != {total_enr}")
            ln = g.get("lower_crosslist")
            num = _course_number(g)
            expected_lower = True if (min_num is None or (num is not None and num == min_num)) else False
            if ln != expected_lower:
                errors.append(f"lower_crosslist mismatch for {crn}: {ln} != {expected_lower}")
    return errors


def validate_conflicts(rows: List[Dict]) -> List[str]:
    errors: List[str] = []
    term_records = {}
    for r in rows:
        term = r.get("term", "").strip()
        term_records.setdefault(term, []).append(r)
    for term, term_rows in term_records.items():
        parsed = []
        for r in term_rows:
            trange = _parse_time_range(r.get("time", ""))
            days = set(_parse_days(r.get("days", "")))
            parsed.append((r, trange, days))
        n = len(parsed)
        expected_map = {id(r): set() for r, _, _ in parsed}
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
                if crn2 in sib1 or crn1 in sib2:
                    continue
                if crn1 and crn2 and crn1 != crn2:
                    expected_map[id(r1)].add(crn2)
                    expected_map[id(r2)].add(crn1)
        for r, _, _ in parsed:
            got = sorted([c for c in (r.get("conflicts", "") or "").split(",") if c])
            expected = sorted(expected_map[id(r)])
            if got != expected:
                errors.append(f"conflicts mismatch for {r.get('crn','')} in term {term}: expected {expected}, got {got}")
    return errors


def main() -> None:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("data/processed/course_all_processed.json")
    rows = load_rows(path)
    errs = []
    errs.extend(validate_crosslist(rows))
    errs.extend(validate_conflicts(rows))
    if errs:
        print(f"Validation failed with {len(errs)} issue(s):")
        for e in errs:
            print("-", e)
        sys.exit(1)
    print(f"Validation passed: {len(rows)} rows checked, no issues found.")


if __name__ == "__main__":
    main()
