# Scraping log

## 2025-12-05
- Initialized scraper work; confirmed site reachable and steps: GET `pducrs.p_duSlctCrsOff` -> POST `pducrs.p_duSlctSubj` -> POST `pducrs.p_duSrchCrsOff`.
- Created `.venv` and installed deps (`requests`, `beautifulsoup4`) via `requirements.txt`.
- Built `scripts/fetch_courses.py` to automate term/college -> subjects -> courses; parses HTML tables into structured rows.
- Test run: `202670` (Autumn Quarter 2026), college `ALL`, subject `COMP` (Computer Science). Output: 102 course rows saved to `data/sample_courses.csv`; preview shows course details (CRN, title, schedule, instructor, seats/enrollment).
- Additional test: `202610` (Winter Quarter 2026), college `ALL`, subject `COMP`. Output: 97 course rows saved to `data/sample_courses.csv`; script flow (term+college -> subjects -> courses) worked.
- Refined parsing: added timeout, user-agent, and logic to attach final exam rows (blank CRN after Lecture/Lecture/Lab/Online/Distance) to the prior course; second consecutive blank row becomes a description/notes string. Updated `data/sample_courses.csv` for `202610`/`ALL`/`COMP` (76 rows now).
- Added optional output path argument to `scripts/fetch_courses.py` (4th positional). Test run for `202630` (Spring Quarter 2026), `ALL`, `COMP` saved 71 rows to `data/sample_courses_spring2026.csv`.
- Added JSON output alongside CSV, with term/college/subject metadata. Runs now emit both CSV and JSON paths. Created combined annual JSON for COMP: `data/json/courses_2026_COMP_all_terms.json` (147 rows from Winter and Spring 2026 runs).
- Created scheduled GitHub Actions workflow `.github/workflows/scrape.yml` (runs twice daily) to scrape `202610` and `202630` COMP data, write CSV/JSON, combine into `data/json/course_COMP_all.json`, and commit changes.
- Added `config.py` to hold term/college/subject constants; workflow now reads from config and combines into `data/json/course_all.json`.
- Added a minimal `README.md` describing source, schedule, outputs, and how to run/adjust terms.
- Added `scripts/process_courses.py` to enrich JSON with crosslist metadata (`crosslist`, `lower-crosslist`, `total_seats`, `total_enrollment`) based on matching time/days/instructor. Outputs go to `data/processed/` with an optional combined processed file.
- Workflow updated to run the processor after scraping. Local run produced `data/processed/course_COMP_202610.json`, `data/processed/course_COMP_202630.json`, and `data/processed/course_all_processed.json`.
- Updated processed totals to be numeric (ints) for consistency. README now notes the processed outputs.
- Clarified crosslist criteria and made `lower-crosslist` true only for the lowest course number within a crosslisted group (or for courses with no siblings).
- Added `conflicts` field (same term/time/days, excluding self and crosslist siblings) to processed JSON. README updated.
- Processor now also writes per-term processed files: `data/processed/term_<term>_processed.json` for each term encountered (e.g., 202610, 202630).
- Normalized time/day/date fields moved into a `normalized` nested object (24h strings, minutes, days list/canonical, ISO dates) to simplify parsing; flat aux fields removed. Validation continues to pass.
