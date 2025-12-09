# DU Course Offerings Scraper

Minimal scraper for the DU “Course Offerings Search” legacy site. It POSTs the same forms as the browser, parses the course table, and writes CSV + JSON.

- Source: https://apps25.du.edu:8446/mdb/pducrs.p_duSlctCrsOff
- Frequency: GitHub Actions runs twice daily (02:00 / 14:00 UTC) via `.github/workflows/scrape.yml`
- Outputs: per-term CSV/JSON in `data/` (e.g., `course_COMP_202610.csv/.json`) and a combined JSON `data/json/course_all.json`
- Processed outputs: `data/processed/` includes enriched JSON (crosslist metadata, group totals) and `data/processed/course_all_processed.json`.
  - Crosslist criteria: same term AND identical time, days, and instructor (all non-empty). `crosslist` lists sibling CRNs; `total_seats`/`total_enrollment` sum the group; `lower-crosslist` is true for the lowest course number in the group (or if no siblings). `conflicts` lists other CRNs in the same term/time/days, excluding the course itself and its crosslist siblings.
  - Per-term processed: `data/processed/term_<term>_processed.json` (e.g., `term_202610_processed.json`, `term_202630_processed.json`)
  - Normalized time/day/date are nested under `normalized`: `time.start_24`/`end_24` and minutes, `days.list`/`canonical`, `dates.start`/`end` (ISO).
  - GTA compatibility matrices: `data/processed/gta_compatibility_term_<term>.csv` list GTA-eligible CRNs as both rows and columns (sorted by course number then section); cells are `TRUE` when the two sections do not time-conflict and `FALSE` when they overlap.
  - Processed JSON rows are sorted by term, then course number, then section/CRN for consistent ordering across files.
  - GTA-only subset JSON: `data/processed/gta_eligible_term_<term>.json` contains GTA-eligible sections with a trimmed field set useful for Power Query (CRN, course/section/title/type, meeting info, room/instructor, seats/enrollment, crosslisted/total enrollment).

Instructor preference history:
- Place legacy instructor preference Excel files in `data/history/excel/` (headers like Term, Course, Section, Instructor, Office Hours, In Class, Grading, Notes).
- Build the consolidated JSON with `python scripts/build_instructor_history.py --input-dir data/history/excel --output data/history/instructor_history.json`.
- Output shape: `{term: {course: {instructor: [entries...]}}}` where each entry captures the preference flags, notes, and source metadata; entries are time-sorted for stability.
- Future files matching `data/history/templates/Faculty GTA Survey template.xlsx` headers (CRN/Course/Sec/Title/Course Type/.../In Class/Office Hours/Grading/Course Notes) are supported; term falls back to parsing the file name (e.g., “Fall 2025”) if no Term column is present.

Course -> title -> instructor map:
- Build with `python scripts/build_course_title_map.py --input data/processed/course_all_processed.json --output data/processed/course_title_instructors.json`.
- Output: nested JSON keyed by course number, then title, with a list of instructors per title.

Course/title/instructor history:
- Build with `python scripts/build_course_instructor_history.py --courses data/processed/course_all_processed.json --history data/history/instructor_history.json --output data/processed/course_instructor_history.json`.
- Output: nested JSON keyed course -> title -> canonical instructor. Each instructor entry includes `display_name`, `aliases` (raw name variants), and `history` (preference entries with term/flags/notes/source). Instructor names are grouped via a simple normalization to reduce duplicates like “Gao, Sky T.” vs “Sky Gao”; aliases are preserved so you can review/resolve collisions.

Configuration:
- Edit `config.py` to change terms, subjects, or college code. TERM codes are kept as constants there for easy updates each term.

Current term codes (config.py):
- `202610` → Winter Quarter 2026
- `202630` → Spring Quarter 2026

Local run example:
```
python scripts/fetch_courses.py 202610 ALL COMP data/course_COMP_202610.csv
```
