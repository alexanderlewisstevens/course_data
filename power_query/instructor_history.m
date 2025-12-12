let
    Source = Json.Document(Web.Contents("https://raw.githubusercontent.com/alexanderlewisstevens/course_data/main/data/processed/course_instructor_history.json")),
    Courses = Record.ToTable(Source),
    #"Renamed Course" = Table.RenameColumns(Courses, {{"Name", "Course"}}),
    #"Titles As Table" = Table.ExpandTableColumn(
        Table.AddColumn(#"Renamed Course", "Titles", each Record.ToTable([Value])),
        "Titles",
        {"Name", "Value"},
        {"Title", "InstructorMap"}
    ),
    #"Instructors As Table" = Table.ExpandTableColumn(
        Table.AddColumn(#"Titles As Table", "InstructorTable", each Record.ToTable([InstructorMap])),
        "InstructorTable",
        {"Name", "Value"},
        {"CanonicalId", "InstructorData"}
    ),
    #"Expanded InstructorData" = Table.ExpandRecordColumn(#"Instructors As Table", "InstructorData", {"display_name", "aliases", "history"}, {"Display Name", "Aliases", "History"}),
    #"Aliases To Text" = Table.TransformColumns(#"Expanded InstructorData", {{"Aliases", each if _ is list then Text.Combine(List.Transform(_, Text.From), ", ") else Text.From(_), type text}}),
    #"Expanded History" = Table.ExpandListColumn(#"Aliases To Text", "History"),
    #"Expanded History Records" = Table.ExpandRecordColumn(#"Expanded History", "History",
        {"term","section","crn","title","office_hours","in_class","grading","time_commitment","notes"},
        {"Term","Sec","CRN","History Title","Office Hours","In Class","Grading","Time Commitment","Notes"}
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
        {"Notes", type text}
    })
in
    #"Typed"
