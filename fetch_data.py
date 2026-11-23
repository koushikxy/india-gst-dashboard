from pathlib import Path

import requests

BASE = "https://tutorial.gst.gov.in/offlineutilities/gst_statistics/statewise_GST_collection_{}.xlsx"
YEARS = ["2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27"]

out = Path("data")
out.mkdir(exist_ok=True)
for y in YEARS:
    r = requests.get(BASE.format(y), headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    (out / f"statewise_GST_collection_{y}.xlsx").write_bytes(r.content)
    print(y, len(r.content))
