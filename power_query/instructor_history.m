let
    Source = Json.Document(Web.Contents("https://raw.githubusercontent.com/alexanderlewisstevens/course_data/main/data/processed/course_instructor_history.json")),
    Courses = Record.ToTable(Source),
    #"Expanded Courses" = Table.ExpandRecordColumn(Courses, "Value", {"Key", "Value"}, {"CourseTitle", "InstructorsByCanon"}),
    #"Renamed Columns" = Table.RenameColumns(#"Expanded Courses",{{"Name","Course"}}),
    #"Expanded CourseTitle" = Table.ExpandRecordColumn(#"Renamed Columns", "CourseTitle", {"Key", "Value"}, {"Title", "InstructorMap"}),
    #"Expanded InstructorMap" = Table.ExpandRecordColumn(#"Expanded CourseTitle", "InstructorMap", {"Key", "Value"}, {"CanonicalId", "InstructorData"}),
    #"Expanded InstructorData" = Table.ExpandRecordColumn(#"Expanded InstructorMap", "InstructorData", {"display_name", "aliases", "history"}, {"Display Name", "Aliases", "History"}),
    #"Expanded History" = Table.ExpandListColumn(#"Expanded InstructorData", "History"),
    #"Expanded History Records" = Table.ExpandRecordColumn(#"Expanded History", "History",
        {"term","section","crn","title","office_hours","in_class","grading","time_commitment","notes","source_file","source_row","instructor","listed_instructor","updated_instructor"},
        {"Term","Sec","CRN","History Title","Office Hours","In Class","Grading","Time Commitment","Notes","Source File","Source Row","Instructor (raw)","Listed Instructor","Updated Instructor"}
    ),
    #"Typed" = Table.TransformColumnTypes(#"Expanded History Records",{
        {"Course", type text},
        {"Title", type text},
        {"CanonicalId", type text},
        {"Display Name", type text},
        {"Aliases", type text},
        {"Term", type text},
        {"Sec", type text},
        {"CRN", type text},
        {"History Title", type text},
        {"Office Hours", type logical},
        {"In Class", type logical},
        {"Grading", type logical},
        {"Time Commitment", type text},
        {"Notes", type text},
        {"Source File", type text},
        {"Source Row", Int64.Type},
        {"Instructor (raw)", type text},
        {"Listed Instructor", type text},
        {"Updated Instructor", type text}
    })
in
    #"Typed"
