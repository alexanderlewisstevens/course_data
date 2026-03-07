# Configuration for scraping targets.
#
# Update TERMS as new term codes become available. Keys are term codes used
# by the DU site; values are human-friendly labels for clarity.
# In CI, terms are discovered dynamically and filtered by year window.
# TERMS is used as a fallback list when live term discovery fails.

TERMS = {
    "202610": "Winter Quarter 2026",
    "202630": "Spring Quarter 2026",
}

# College code to use in the form POST.
COLLEGE = "ALL"

# Subject codes to scrape (e.g., "COMP", "MATH").
SUBJECTS = ["COMP"]
