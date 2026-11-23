section Section1;

shared gst =
let
    Source = Folder.Files(DataFolder),
    Files = Table.SelectRows(Source, each Text.StartsWith([Name], "statewise_GST_collection_") and [Extension] = ".xlsx"),
    Read = Table.AddColumn(Files, "rows", each fnReadYear([Content])),
    Combined = Table.Combine(Read[rows]),
    Typed = Table.TransformColumnTypes(Combined, {{"month", type date}, {"state_code", Int64.Type}, {"tax_head", type text}, {"amount_cr", type number}})
in
    Typed;

shared fnReadYear =
(content as binary) as table =>
let
    sheet = Excel.Workbook(content, null, true){[Item = "Collections-Statewise", Kind = "Sheet"]}[Data],
    firstCol = List.Transform(sheet[Column1], each try Text.Lower(Text.Trim(_)) otherwise ""),
    headerRow = List.PositionOf(firstCol, "state cd"),
    toMonth = (v) => if v is date or v is datetime then Date.From(v) else try Date.FromText(Text.From(v), [Format = "MMM-yy", Culture = "en-US"]) otherwise null,
    monthCells = Record.FieldValues(sheet{headerRow}),
    taxCells = Record.FieldValues(sheet{headerRow + 1}),
    months = List.Skip(List.Accumulate(monthCells, {null}, (s, v) => s & {if v = null then List.Last(s) else toMonth(v)}), 1),
    header = Table.FromColumns({Table.ColumnNames(sheet), months, taxCells}, {"col", "month", "tax_head"}),
    keep = Table.SelectRows(header, each [month] <> null and List.Contains({"CGST", "SGST", "IGST"}, [tax_head])),
    body = Table.Skip(sheet, headerRow + 2),
    stateRows = Table.SelectRows(body, each (try Number.From(Text.Trim(Text.From([Column1]))) otherwise null) <> null),
    withCode = Table.AddColumn(stateRows, "state_code", each Number.From(Text.Trim(Text.From([Column1]))), Int64.Type),
    long = Table.UnpivotOtherColumns(Table.SelectColumns(withCode, {"state_code"} & keep[col]), {"state_code"}, "col", "raw"),
    joined = Table.Join(long, "col", keep, "col"),
    amount = Table.AddColumn(joined, "amount_cr", each try Number.From([raw]) otherwise null, type nullable number),
    result = Table.SelectColumns(Table.SelectRows(amount, each [amount_cr] <> null), {"month", "state_code", "tax_head", "amount_cr"})
in
    result;

shared states =
let
    Source = Csv.Document(File.Contents(DataFolder & "\states.csv"), [Delimiter = ",", Encoding = 65001]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Headers, {{"state_code", Int64.Type}, {"state", type text}, {"zone", type text}, {"state_type", type text}})
in
    Typed;

shared tax_heads =
let
    Source = #table(
        type table [tax_head = text, tax_name = text, goes_to = text, head_order = Int64.Type],
        {
            {"CGST", "Central GST", "Centre", 1},
            {"SGST", "State GST", "State", 2},
            {"IGST", "Integrated GST", "Split after settlement", 3}
        }
    )
in
    Source;
