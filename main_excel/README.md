# Excel Power Query setup (SharePoint, consolidated workbook)

We now publish a consolidated read-only workbook `Master_All_Terms.xlsx` (built via `scripts/build_master_all_terms.py`). Each term is a separate sheet (reverse chronological). Connect Power Query to the sheet you need.

## Steps (once per workbook)
1) Upload `data/exports/Master_All_Terms.xlsx` to your SharePoint/OneDrive library (or use the per-term `data/exports/<term>/Master_PQ.xlsx` if you only need one term).
2) In Excel: Data → Get Data → From File → From SharePoint Folder → pick `Master_All_Terms.xlsx`.
3) In Power Query Navigator: select the sheet named with the term code you need (e.g., `202610`), then load.
4) Set column types as needed; Close & Load.
5) Refresh settings: enable refresh on open/interval and use your organizational credentials.

## Using the provided M script
If you prefer to paste a query:
1) Data → Get Data → From Other Sources → Blank Query.
2) Advanced Editor → replace contents with `main_excel/query_course_all.m`.
   - Update `SourceUrl` to your SharePoint URL for `Master_All_Terms.xlsx`.
   - Update the `Item="202610"` to the term sheet you want.
3) Save and load.

## Updating the source later
- Rebuild `Master_All_Terms.xlsx` with `python scripts/build_master_all_terms.py` after refreshing processed data.
- Re-upload/overwrite the file in SharePoint; PQ connections will continue to work if the path stays the same.

## Where to store Power Query (.m) scripts

Keep the `.m` files in one predictable spot so they are easy to find and audit. Suggested layout:

```
power_query/
  master_all_terms.m   // Base query for Master_All_Terms.xlsx; source: data/processed/course_all_processed.json
  course_all_raw.m     // Raw course_all.json (if you need unprocessed data)
```

Tips:
- Name each `.m` after the workbook/tab it feeds and include a comment at the top with the source URL (raw GitHub or SharePoint).
- For multi-sheet workbooks like `Master_All_Terms.xlsx`, keep one base query (e.g., `AllGTA`) and create reference queries per term to fan out to sheets.
