let
    Url =
        "https://raw.githubusercontent.com/alexanderlewisstevens/course_data/refs/heads/main/data/processed/course_instructor_history.json",

    Source = Json.Document(
        Web.Contents(
            Url,
            [Headers=[Accept="application/json", #"User-Agent"="Excel-PowerQuery"]]
        )
    ),

    Courses = Record.ToTable(Source),
    CoursesRenamed = Table.RenameColumns(Courses, {{"Name","Course"}, {"Value","TitlesRecord"}}),

    TitlesToRows = Table.AddColumn(CoursesRenamed, "TitlesTable", each Record.ToTable([TitlesRecord])),
    TitlesExpanded = Table.ExpandTableColumn(TitlesToRows, "TitlesTable", {"Name","Value"}, {"CourseTitle","InstructorsRecord"}),

    InstructorsToRows = Table.AddColumn(TitlesExpanded, "InstructorsTable", each Record.ToTable([InstructorsRecord])),
    InstructorsExpanded = Table.ExpandTableColumn(InstructorsToRows, "InstructorsTable", {"Name","Value"}, {"InstructorKey","InstructorRecord"}),

    InstructorFields = Table.ExpandRecordColumn(
        InstructorsExpanded,
        "InstructorRecord",
        {"display_name","history"},
        {"DisplayName","History"}
    ),

    HistoryNormalized = Table.TransformColumns(
        InstructorFields,
        {{"History", each if _ is list and List.Count(_) = 0 then {null} else _, type list}}
    ),

    HistoryToRows = Table.ExpandListColumn(HistoryNormalized, "History"),

    HistoryExpanded = Table.ExpandRecordColumn(
        HistoryToRows,
        "History",
        {"term","section","crn","title","office_hours","in_class","grading","time_commitment","notes"},
        {"Term","Section","CRN","HistTitle","OfficeHours","InClass","Grading","TimeCommitment","Notes"}
    ),

    RemovedContainers = Table.RemoveColumns(HistoryExpanded, {"TitlesRecord","InstructorsRecord"}),

    Typed = Table.TransformColumnTypes(
        RemovedContainers,
        {
            {"Course", type text},
            {"CourseTitle", type text},
            {"InstructorKey", type text},
            {"DisplayName", type text},
            {"Term", type text},
            {"Section", type text},
            {"CRN", type text},
            {"HistTitle", type text},
            {"OfficeHours", type logical},
            {"InClass", type logical},
            {"Grading", type logical},
            {"TimeCommitment", type text},
            {"Notes", type text}
        }
    ),

    Reordered = Table.ReorderColumns(
        Typed,
        {"Course","CourseTitle","InstructorKey","DisplayName","Term","Section","CRN","HistTitle","OfficeHours","InClass","Grading","TimeCommitment","Notes"}
    ),

    Final = Table.Buffer(Reordered)
in
    Final
