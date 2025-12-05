# DU Course Offerings Scraper

Minimal scraper for the DU “Course Offerings Search” legacy site. It POSTs the same forms as the browser, parses the course table, and writes CSV + JSON.

- Source: https://apps25.du.edu:8446/mdb/pducrs.p_duSlctCrsOff
- Frequency: GitHub Actions runs twice daily (02:00 / 14:00 UTC) via `.github/workflows/scrape.yml`
- Outputs: per-term CSV/JSON in `data/` (e.g., `course_COMP_202610.csv/.json`) and a combined JSON `data/json/course_all.json`

Configuration:
- Edit `config.py` to change terms, subjects, or college code. TERM codes are kept as constants there for easy updates each term.

Current term codes (config.py):
- `202610` → Winter Quarter 2026
- `202630` → Spring Quarter 2026

Local run example:
```
python scripts/fetch_courses.py 202610 ALL COMP data/course_COMP_202610.csv
```
