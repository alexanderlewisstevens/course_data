# DU Course Offerings Scraper

Minimal scraper for the DU “Course Offerings Search” legacy site. It POSTs the same forms as the browser, parses the course table, and writes CSV + JSON.

- Source: https://apps25.du.edu:8446/mdb/pducrs.p_duSlctCrsOff
- Frequency: GitHub Actions runs twice daily (02:00 / 14:00 UTC) via `.github/workflows/scrape.yml`.
- Outputs: per-term CSV/JSON in `data/raw/` (e.g., `course_COMP_202610.csv/.json`) and a combined raw JSON `data/json/course_all.json`.
- Processed outputs: `data/processed/course_all_processed.json` (master). Enrichments include:
  - Crosslists: same term AND identical time/days/instructor. Fields: `crosslist` (siblings), `crosslisted_crn` (self + siblings), `crosslisted_enrollment`, `total_enrollment`, `total_seats`, `lower_crosslist`.
  - Conflicts: `conflicts` lists same-term CRNs with overlapping time windows and days (excluding crosslist siblings).
  - GTA flag: `gta_eligible` is true when seats > 0 and course_type contains lecture/lab/online/distance.
  - Time/day helpers: flattened `time_start_24`/`time_end_24`, `time_start_minutes`/`time_end_minutes`, `days_canonical`/`days_list`, `date_start`/`date_end`, plus the nested `normalized` block.
  - Rows are sorted by term, then course number, then section/CRN for consistency.

Project layout (lean):
- `data/raw/`: per-term scrapes.
- `data/json/`: combined raw (`course_all.json`, optional).
- `data/processed/`: `course_all_processed.json` (master feed), `course_instructor_history.json`, `course_title_instructors.json`.
- `data/history/`: instructor survey inputs (`excel/`), templates (`templates/`), consolidated `instructor_history.json`.
- `data/exports/`: `Master_All_Terms.xlsx` (optional workbook artifact).
- `power_query/`: `master_all_terms.m` (base PQ script).
- `src/`: processing code (`pipeline.py`); `scripts/` are thin wrappers.

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

Power Query:
- Base M script lives in `power_query/master_all_terms.m` and pulls `data/processed/course_all_processed.json` (fields above) into Excel. Use per-term reference queries or `FILTER` sheets for separate tabs.

Configuration:
- Edit `config.py` to change terms, subjects, or college code. TERM codes are kept as constants there for easy updates each term.

Current term codes (config.py):
- `202610` → Winter Quarter 2026
- `202630` → Spring Quarter 2026

Local run example:
```
python scripts/fetch_courses.py 202610 ALL COMP data/raw/course_COMP_202610.csv
python scripts/process_courses.py --outdir data/processed --combine data/processed/course_all_processed.json
```
