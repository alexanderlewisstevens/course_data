# Data Flows and Outputs

## Course data pipeline (master)
```mermaid
flowchart TB
  src[DU Course Offerings site] --> fetch[fetch_courses.py\nper-term scrape]
  fetch --> raw[data/raw/course_COMP_{term}.csv\nand .json]
  raw --> combo[data/json/course_all.json\n(combined raw, optional)]
  combo --> proc[src/pipeline.py (process_courses.py)\nnormalize + crosslists\nconflicts + GTA flag]
  proc --> allProc[data/processed/course_all_processed.json\n(sorted, typed, flattened time/day helpers)]
  allProc --> pq[power_query/master_all_terms.m\nPower Query base]
  pq --> excel[Excel workbook\n(master/all terms)]
```
- Processed JSON includes crosslist fields (`crosslist`, `crosslisted_crn`, `crosslisted_enrollment`, `total_enrollment`, `total_seats`, `lower_crosslist`), conflicts, GTA flag, and flattened time/day/date fields.

## Instructor history and mappings
```mermaid
flowchart TB
  histXlsx[data/history/excel/*.xlsx] --> histBuilder[build_instructor_history.py]
  histBuilder --> histJson[data/history/instructor_history.json]
  allProc[data/processed/course_all_processed.json] --> titleMap[build_course_title_map.py]
  titleMap --> titleOut[data/processed/course_title_instructors.json\n(course -> title -> instructors)]
  allProc --> histMerge[build_course_instructor_history.py]
  histJson --> histMerge
  histMerge --> courseHist[data/processed/course_instructor_history.json\n(course -> title -> instructor history)]
```
- History JSON is the consolidated record of faculty GTA preference files.
- Course/instructor history merges processed courses with historical preferences for downstream review.
