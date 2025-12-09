# DU Course Offerings Scraper

Minimal scraper for the DU “Course Offerings Search” legacy site. It POSTs the same forms as the browser, parses the course table, and writes CSV + JSON.

- Source: https://apps25.du.edu:8446/mdb/pducrs.p_duSlctCrsOff
- Frequency: GitHub Actions runs twice daily (02:00 / 14:00 UTC) via `.github/workflows/scrape.yml`
- Outputs: per-term CSV/JSON in `data/` (e.g., `course_COMP_202610.csv/.json`) and a combined JSON `data/json/course_all.json`
- Processed outputs: `data/processed/` includes enriched JSON (crosslist metadata, group totals) and `data/processed/course_all_processed.json`.
  - Crosslist criteria: same term AND identical time, days, and instructor (all non-empty). `crosslist` lists sibling CRNs; `total_seats`/`total_enrollment` sum the group; `lower-crosslist` is true for the lowest course number in the group (or if no siblings). `conflicts` lists other CRNs in the same term/time/days, excluding the course itself and its crosslist siblings.
  - Per-term processed: `data/processed/term_<term>_processed.json` (e.g., `term_202610_processed.json`, `term_202630_processed.json`)
  - Normalized time/day/date are nested under `normalized`: `time.start_24`/`end_24` and minutes, `days.list`/`canonical`, `dates.start`/`end` (ISO).

Configuration:
- Edit `config.py` to change terms, subjects, or college code. TERM codes are kept as constants there for easy updates each term.

Current term codes (config.py):
- `202610` → Winter Quarter 2026
- `202630` → Spring Quarter 2026

Local run example:
```
python scripts/fetch_courses.py 202610 ALL COMP data/course_COMP_202610.csv
```
