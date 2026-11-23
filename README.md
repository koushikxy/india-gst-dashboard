# India's GST collections by state

GST collections are reported every month as one big all-India number. I wanted to see which states that money actually comes from, whether the gap between the big states and the rest is changing, and how fast collections are still growing. So I built a Power BI dashboard from the GST portal's state-wise collection files, covering July 2017 (when GST started) to September 2026.

![Overview](screenshots/overview.png)

## Findings

All numbers are domestic GST (CGST + SGST + IGST) collected in each state, in ₹ crore. I used 2018-19 as the base year because it is the first full year of GST.

Collections roughly doubled, from ₹7.89 lakh crore in 2018-19 to ₹16.32 lakh crore in 2025-26 (+107%).

But growth has slowed every year since the post-lockdown rebound: 26.9% in 2021-22, then 20.9%, 15.2%, 10.3% and 6.4% in 2025-26. April to September 2026 was 6.1% higher than the same months of 2025.

![Trend](screenshots/trend.png)

November 2025 was 2.3% lower than November 2024. That was the first month below the year before since June 2021, and May 2026 dipped again (-2.6%). The November fall came soon after the GST rate cuts of 22 September 2025, but this data alone can't tell how much of the dip is because of them. July to September 2026 were back to about 9-10% growth.

The 2020 lockdown is easy to spot: April 2020 collections were ₹18,974 crore against ₹75,674 crore in February 2020, 77% below April 2019.

The big states' share is growing. The top 5 states had 52.2% of the total in 2018-19 and 55.6% in 2025-26. Maharashtra alone went from 20.1% to 22.2%. Karnataka moved past Gujarat into second place.

![States](screenshots/states.png)

Among the 15 biggest states, growth from 2018-19 to 2025-26 ranged from +69% (Andhra Pradesh) to +141% (Odisha). Haryana (+136%), Karnataka (+130%) and Maharashtra (+128%) grew faster than India as a whole, while West Bengal (+82%) and Rajasthan (+84%) grew slower.

The split between tax heads hardly moved: in 2025-26 IGST was 39%, SGST 34% and CGST 27%, close to the 2018-19 split.

## Data

The source is the [GST statistics page](https://www.gst.gov.in/download/gststatistics) on the GST portal, which has one Excel file per financial year ("State-wise GST collection"), 10 files from 2017-18 to 2026-27. `fetch_data.py` downloads them into `data/`. The files are small, so they are in the repo.

The files look similar but are not the same:

- The layout is a pivot table with merged headers. Each month is a block of columns, and the month name sits only in the first column of the block, so it has to be filled across before the columns mean anything.
- The first block in every file is the year total, labelled "Financial Year 2017-18" in some files, "TOTAL" in 2019-20 and "Financial Year (up to the Month - Mar 2025)" in later ones.
- Month headers are real dates in most files, but April 2018 is the text `Apr-18`.
- Up to 2024-25 each month has 5 columns (CGST, SGST, IGST, CESS, TOTAL). From 2025-26 the CESS column is gone and each month has 4. I left cess out of everything so the years compare like for like.
- The sheet I need is the only sheet in the first three files and the second of three sheets after that, so it is picked by name (`Collections-Statewise`).
- State codes are numbers in some files and text with a leading zero (`01`) in others.
- Names change across files: `Andaman and Nicobar Island` vs `Islands`, the code 99 row is `CBIC` in early files and `OIDAR` later, and the header is `State Cd` or `State CD`.
- Daman and Diu (code 25) and Dadra and Nagar Haveli (code 26) are separate rows up to 2025-26, even after the two were merged in 2020. The 2026-27 file has only code 26. `data/states.csv` maps both codes to the merged UT. Ladakh (code 38) appears from 2019-20.
- Totals and footnote rows have to be dropped: `Grand Total` or `Domestic GST Collection- All India`, `Gross Revenue`, and `IGST and CESS on Import - All India` (just `IGST on Import - All India` in 2026-27). Two files also have a stray `s` typed in an empty column next to Jharkhand.
- July 2017 is almost zero for every state, because GST for July was paid in August.

`states.csv` is the only file I made by hand. It gives each state code a clean name, a zone (based loosely on the Zonal Councils) and whether it is a state or UT.

All the cleaning is in Power Query: `fnReadYear` reads one file and `gst` combines the folder. It ends with 12,849 rows (state x month x tax head). `check_numbers.py` reads the same files separately with pandas and works out every number in this README, saved in `facts.json`. I checked the dashboard measures against it, and also checked that CGST + SGST + IGST + CESS equals the TOTAL column in every state and month (it does).

## Model and measures

`gst` has one row per state, month and tax head. It links to `states` (name, zone, state or UT), `tax_heads`, and a DAX `Calendar` table with April-to-March financial year columns, marked as the date table.

`GST (Cr)` is a plain SUM, and the other measures build on it. `Share of India` divides by the same total with the state filter removed. `YoY %` uses `SAMEPERIODLASTYEAR`. Because the calendar ends in September 2026, 2026-27 is compared April-September with April-September. It is left blank when the earlier period has fewer months of data, or when last year's figure is almost zero, so 2018-19 has no growth figure. `Top 5 Share` adds up the five largest states with `TOPN`, and `Growth vs FY 2018-19` swaps the year filter for 2018-19 to get the base.

The Overview page has the yearly and monthly totals. Growth by state and tax head is on the Trend page, and the States page ranks every state for the year picked.

## Files

- `gst_dashboard.pbip` with the `gst_dashboard.SemanticModel` and `gst_dashboard.Report` folders: the Power BI project. The model is stored as TMDL text files and the report pages as JSON.
- `queries.pq` and `measures.dax`: copies of the M queries and the DAX (calendar table and measures), so the logic can be read without opening Power BI.
- `gst_dashboard.pdf`: an export of the three report pages.
- `fetch_data.py` downloads the yearly files and `check_numbers.py` recounts every figure in pandas. They need `requests`, `openpyxl` and `pandas`.
- `data/`: the downloaded files plus my `states.csv` lookup.

The `DataFolder` parameter is set to `C:\gst\data`. Before refreshing, either copy the `data` folder there or point the parameter at your own copy (Transform data, then Edit parameters).

## Limits

These are collections by the state where tax was paid, before IGST is settled between the Centre and states, so they are not the same as each state's GST revenue. Import IGST is not split by state in these files, so it is not included.

The figures are provisional, as the files themselves say, and 2026-27 only runs to September. Leaving cess out means my totals are lower than the gross GST figures in the news.

The late-2025 dip only lines up with the rate cuts in time. I haven't checked other causes such as refunds or changes in compliance.

Tools: Power BI Desktop, Power Query (M), DAX, Python (pandas) for checking
