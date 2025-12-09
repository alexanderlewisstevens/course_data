# Excel Power Query setup (SharePoint-friendly)

Use these steps to connect an Excel workbook (stored in SharePoint/OneDrive) to the public course JSON and refresh it automatically.

Public feed (combined):  
`https://raw.githubusercontent.com/alexanderlewisstevens/course_data/main/data/json/course_all.json`

If you prefer single-term feeds, swap the URL to one of:
- Winter 2026: `https://raw.githubusercontent.com/alexanderlewisstevens/course_data/main/data/course_COMP_202610.json`
- Spring 2026: `https://raw.githubusercontent.com/alexanderlewisstevens/course_data/main/data/course_COMP_202630.json`

## Steps (once per workbook)
1) Create or open a workbook in the SharePoint/OneDrive library where you want it to live.
2) Data → Get Data → From Web → Advanced → paste the combined JSON URL above → OK.
3) In Power Query:
   - Navigator: select the list, then “To Table.”
   - Expand all columns.
   - Set column types (keep `term` and `crn` as Text).
   - Close & Load to a table.
4) Refresh settings:
   - Data → Queries & Connections → Properties → enable “Refresh every X minutes” (optional) and “Refresh data when opening the file.”
   - If SharePoint prompts, choose Anonymous/Organizational as appropriate (raw.githubusercontent.com is public).

## Using the provided M script
If you prefer to paste a query:
1) Data → Get Data → From Other Sources → Blank Query.
2) Advanced Editor → replace contents with `main_excel/query_course_all.m`.
3) Save and load as above.

## Updating the source later
- If terms/subjects change, the GitHub Actions workflow will refresh the JSON on the schedule. Your workbook will pick up new rows on refresh as long as the URL stays the same.
- If the repo branch changes from `main`, update the URL to match.
