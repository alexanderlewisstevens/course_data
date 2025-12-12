let
    // Read URLs from the Sources table on the Config sheet
    Sources = Excel.CurrentWorkbook(){[Name="Sources"]}[Content],
    MasterUrl = try Sources{[Name="MasterUrl"]}[Url] otherwise "https://denveru.sharepoint.com/:x:/r/sites/CSDepartment-g/Shared%20Documents/General/Committees/GTA%20Committee/Master_All_Terms.xlsx?d=wc91eb6e4bac0479abbd0a9b7472671e4&csf=1&web=1&e=ZLuvMD",
    HistoryUrl = Sources{[Name="HistoryUrl"]}[Url],

    // Load master (course) data from Excel workbook hosted at MasterUrl
    MasterWorkbook = Excel.Workbook(Web.Contents(MasterUrl), null, true),
    // Adjust Item/Kind to match the sheet or table name that holds the master data
    MasterData = MasterWorkbook{[Item="ALLGTA",Kind="Sheet"]}[Data],
    MasterHeaders = Table.PromoteHeaders(MasterData, [PromoteAllScalars=true]),
    MasterTyped = Table.TransformColumnTypes(MasterHeaders,{
        {"Term", type text},{"CRN", type text},{"Course", type text},{"Sec", type text},
        {"Title", type text},{"Course Type", type text},{"Meeting Dates", type text},
        {"Time", type text},{"Days", type text},{"Hrs", type text},{"Room", type text},
        {"Instructor", type text},{"Seat", Int64.Type},{"Enr", Int64.Type},
        {"Crosslist", type text},{"Crosslisted Enr", Int64.Type},{"Total Enr", Int64.Type},
        {"Conflicts", type text},{"gta_eligible", type logical}
    }),

    // Apply optional filters from Keys table (Term/Course/Sec)
    Keys = Excel.CurrentWorkbook(){[Name="Keys"]}[Content],
    Terms = List.RemoveNulls(Keys[Term]),
    Courses = List.RemoveNulls(Keys[Course]),
    Secs = List.RemoveNulls(Keys[Sec]),
    MasterFiltered = Table.SelectRows(MasterTyped, each
        (List.IsEmpty(Terms) or List.Contains(Terms, [Term])) and
        (List.IsEmpty(Courses) or List.Contains(Courses, [Course])) and
        (List.IsEmpty(Secs) or List.Contains(Secs, [Sec]))
    ),

    // Load instructor history JSON
    HistoryJson = Json.Document(Web.Contents(HistoryUrl)),
    CoursesTable = Record.ToTable(HistoryJson),
    RenamedCourse = Table.RenameColumns(CoursesTable, {{"Name", "Course"}}),
    TitlesAsTable = Table.ExpandTableColumn(
        Table.AddColumn(RenamedCourse, "Titles", each Record.ToTable([Value])),
        "Titles", {"Name", "Value"}, {"Title", "InstructorMap"}
    ),
    InstructorsAsTable = Table.ExpandTableColumn(
        Table.AddColumn(TitlesAsTable, "InstructorTable", each Record.ToTable([InstructorMap])),
        "InstructorTable", {"Name", "Value"}, {"CanonicalId", "InstructorData"}
    ),
    ExpandedInstructorData = Table.ExpandRecordColumn(InstructorsAsTable, "InstructorData", {"display_name", "aliases", "history"}, {"Display Name", "Aliases", "History"}),
    AliasesToText = Table.TransformColumns(ExpandedInstructorData, {{"Aliases", each if _ is list then Text.Combine(List.Transform(_, Text.From), ", ") else Text.From(_), type text}}),
    ExpandedHistory = Table.ExpandListColumn(AliasesToText, "History"),
    ExpandedHistoryRecords = Table.ExpandRecordColumn(ExpandedHistory, "History",
        {"term","section","crn","title","office_hours","in_class","grading","time_commitment","notes"},
        {"Term","Sec","CRN","History Title","Office Hours","In Class","Grading","Time Commitment","Notes"}
    ),
    HistoryTyped = Table.TransformColumnTypes(ExpandedHistoryRecords,{
        {"Course", type text},{"Title", type text},{"CanonicalId", type text},{"Display Name", type text},{"Aliases", type text},
        {"Term", type text},{"Sec", type text},{"CRN", type text},{"History Title", type text},
        {"Office Hours", type logical},{"In Class", type logical},{"Grading", type logical},{"Time Commitment", type text},{"Notes", type text}
    }),

    // Apply optional filters from HistoryKeys table
    HistoryKeys = Excel.CurrentWorkbook(){[Name="HistoryKeys"]}[Content],
    HKCourses = List.RemoveNulls(HistoryKeys[Course]),
    HKTitles = List.RemoveNulls(HistoryKeys[Title]),
    HKTerms = List.RemoveNulls(HistoryKeys[Term]),
    HKInstr = List.RemoveNulls(HistoryKeys[Instructor]),
    HistoryFiltered = Table.SelectRows(HistoryTyped, each
        (List.IsEmpty(HKCourses) or List.Contains(HKCourses, [Course])) and
        (List.IsEmpty(HKTitles) or List.Contains(HKTitles, [Title])) and
        (List.IsEmpty(HKTerms) or List.Contains(HKTerms, [Term])) and
        (List.IsEmpty(HKInstr) or List.Contains(HKInstr, [Display Name]))
    )
in
    [Master = MasterFiltered, History = HistoryFiltered]
