let
    SourceUrl = "https://raw.githubusercontent.com/alexanderlewisstevens/course_data/main/data/json/course_all.json",
    Source = Json.Document(Web.Contents(SourceUrl)),
    #"Converted to Table" = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Expanded Column" = Table.ExpandRecordColumn(#"Converted to Table", "Column1", {"term", "college", "subject_code", "subject_label", "crn", "course", "section", "title", "course_type", "meeting_dates", "time", "days", "hours", "room", "instructor", "seats", "enrolled", "exam_meeting_dates", "exam_time", "exam_days", "exam_room", "description"}, {"term", "college", "subject_code", "subject_label", "crn", "course", "section", "title", "course_type", "meeting_dates", "time", "days", "hours", "room", "instructor", "seats", "enrolled", "exam_meeting_dates", "exam_time", "exam_days", "exam_room", "description"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Expanded Column",{{"term", type text}, {"college", type text}, {"subject_code", type text}, {"subject_label", type text}, {"crn", type text}, {"course", type text}, {"section", type text}, {"title", type text}, {"course_type", type text}, {"meeting_dates", type text}, {"time", type text}, {"days", type text}, {"hours", type text}, {"room", type text}, {"instructor", type text}, {"seats", type text}, {"enrolled", type text}, {"exam_meeting_dates", type text}, {"exam_time", type text}, {"exam_days", type text}, {"exam_room", type text}, {"description", type text}})
in
    #"Changed Type"
