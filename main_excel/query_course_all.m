let
    // Replace with your SharePoint file URL for Master_All_Terms.xlsx
    SourceUrl = "https://<tenant>.sharepoint.com/sites/<site>/Shared%20Documents/<path>/Master_All_Terms.xlsx",
    Source = Excel.Workbook(Web.Contents(SourceUrl), null, true),
    // Replace the Item name with the term sheet you want (e.g., 202610)
    TermSheet = Source{[Item="202610",Kind="Sheet"]}[Data],
    #"Promoted Headers" = Table.PromoteHeaders(TermSheet, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"Term", type text}, {"CRN", type text}, {"Course", type text}, {"Sec", type text}, {"Title", type text}, {"Course Type", type text}, {"Meeting Dates", type text}, {"Time", type text}, {"Days", type text}, {"Hrs", type text}, {"Room", type text}, {"Instructor", type text}, {"Seat", Int64.Type}, {"Enr", Int64.Type}, {"Crosslisted Enr", Int64.Type}, {"Total Enr", Int64.Type}, {"Prefer TA 1", type text}, {"Prefer TA 2", type text}, {"Prefer TA 3", type text}, {"In Class", type text}, {"Office Hours", type text}, {"Grading", type text}, {"Time commitment", type text}, {"Notes", type text}})
in
    #"Changed Type"
