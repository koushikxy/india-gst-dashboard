import glob
import json
from datetime import datetime

import openpyxl
import pandas as pd

rows = []
for path in sorted(glob.glob("data/statewise_GST_collection_*.xlsx")):
    ws = openpyxl.load_workbook(path, data_only=True)["Collections-Statewise"]
    grid = [list(r) for r in ws.iter_rows(values_only=True)]
    h = next(i for i, r in enumerate(grid) if isinstance(r[0], str) and r[0].strip().lower() == "state cd")
    month, heads = None, []
    for m, t in zip(grid[h], grid[h + 1]):
        if m is not None:
            month = m
            if isinstance(month, str):
                try:
                    month = datetime.strptime(month, "%b-%y")
                except ValueError:
                    pass
        heads.append((month if isinstance(month, datetime) else None, t))
    for r in grid[h + 2:]:
        try:
            code = int(str(r[0]).strip())
        except ValueError:
            continue
        for j, (m, t) in enumerate(heads):
            if m is not None and t in ("CGST", "SGST", "IGST", "CESS", "TOTAL") and isinstance(r[j], (int, float)):
                rows.append({"code": code, "month": m, "head": t, "amount": float(r[j])})

raw = pd.DataFrame(rows)
wide = raw.pivot_table(index=["code", "month"], columns="head", values="amount", aggfunc="sum")
total_gap = (wide[["CGST", "SGST", "IGST"]].sum(axis=1) + wide["CESS"].fillna(0) - wide["TOTAL"]).abs().max()

states = pd.read_csv("data/states.csv")
df = raw[raw["head"].isin(["CGST", "SGST", "IGST"])].merge(states, left_on="code", right_on="state_code")
df["fy_start"] = df["month"].dt.year - (df["month"].dt.month < 4)
df["fy"] = df["fy_start"].astype(str) + "-" + (df["fy_start"] + 1).astype(str).str[2:]

fy = df.groupby("fy")["amount"].sum()
st = df.groupby(["fy", "state"])["amount"].sum().unstack(0)
m = df.groupby("month")["amount"].sum().sort_index()
yoy = m / m.shift(12) - 1
h1 = df[df["month"].dt.month.between(4, 9)].groupby("fy")["amount"].sum()
heads = df.groupby(["fy", "head"])["amount"].sum().unstack()


def top5(y):
    s = st[y].sort_values(ascending=False)
    return s.head(5).sum() / s.sum()


big15 = st["2025-26"].sort_values(ascending=False).head(15).index
growth = (st["2025-26"] / st["2018-19"] - 1)[big15].sort_values()

facts = {
    "fact_rows": [len(df), "len(df) after keeping CGST, SGST, IGST cells with a number; Power BI COUNTROWS(gst)"],
    "max_gap_components_vs_total_cr": [round(total_gap, 4), "abs(CGST+SGST+IGST+CESS - TOTAL) per state-month, max"],
    "fy_2018_19_lakh_cr": [round(fy["2018-19"] / 1e5, 2), "fy['2018-19'] / 1e5; [GST (Lakh Cr)] for FY 2018-19"],
    "fy_2025_26_lakh_cr": [round(fy["2025-26"] / 1e5, 2), "fy['2025-26'] / 1e5; [GST (Lakh Cr)] for FY 2025-26"],
    "growth_fy19_to_fy26": [round(fy["2025-26"] / fy["2018-19"] - 1, 4), "fy['2025-26'] / fy['2018-19'] - 1"],
    "fy_yoy": [{k: round(v, 4) for k, v in fy.pct_change().dropna().items() if k not in ("2018-19", "2026-27")}, "fy.pct_change(); [YoY %] by FY. 2018-19 is left blank because 2017-18 has only 9 months"],
    "h1_2026_27_yoy": [round(h1["2026-27"] / h1["2025-26"] - 1, 4), "Apr-Sep 2026 vs Apr-Sep 2025; [YoY %] / [FYTD YoY %] for FY 2026-27"],
    "monthly_avg_2025_26_cr": [round(fy["2025-26"] / 12), "fy['2025-26'] / 12; [Monthly Avg (Cr)]"],
    "top5_share_2018_19": [round(top5("2018-19"), 4), "top 5 states / all; [Top 5 Share]"],
    "top5_share_2025_26": [round(top5("2025-26"), 4), "top 5 states / all; [Top 5 Share]"],
    "maharashtra_share_2018_19": [round(st.loc["Maharashtra", "2018-19"] / fy["2018-19"], 4), "[Share of India] for Maharashtra"],
    "maharashtra_share_2025_26": [round(st.loc["Maharashtra", "2025-26"] / fy["2025-26"], 4), "[Share of India] for Maharashtra"],
    "top5_states_2025_26": [list(st["2025-26"].sort_values(ascending=False).head(5).index), "[State Rank] 1-5"],
    "growth_vs_2018_19_big15": [{k: round(v, 4) for k, v in growth.items()}, "st['2025-26'] / st['2018-19'] - 1; [Growth vs FY 2018-19]"],
    "apr_2020_cr": [round(m["2020-04-01"]), "monthly total April 2020"],
    "feb_2020_cr": [round(m["2020-02-01"]), "monthly total February 2020"],
    "apr_2020_yoy": [round(yoy["2020-04-01"], 4), "[YoY %] April 2020"],
    "apr_2021_yoy": [round(yoy["2021-04-01"], 4), "[YoY %] April 2021"],
    "nov_2025_yoy": [round(yoy["2025-11-01"], 4), "[YoY %] November 2025"],
    "negative_yoy_months_since_2021": [[str(k.date()) for k in yoy[yoy < 0]["2021-01-01":].index], "months where [YoY %] is below zero"],
    "may_2026_yoy": [round(yoy["2026-05-01"], 4), "[YoY %] May 2026"],
    "jul_to_sep_2026_yoy": [{str(k.date()): round(v, 4) for k, v in yoy["2026-07-01":].items()}, "[YoY %] July-September 2026"],
    "sep_2026_cr": [round(m["2026-09-01"]), "[GST (Cr)] September 2026"],
    "sep_2026_mom": [round(m["2026-09-01"] / m["2026-08-01"] - 1, 4), "[MoM %] September 2026"],
    "rolling_12m_sep_2026_lakh_cr": [round(m["2025-10-01":"2026-09-01"].sum() / 1e5, 4), "[Rolling 12M (Lakh Cr)] at September 2026"],
    "avg_3m_sep_2026_lakh_cr": [round(m["2026-07-01":"2026-09-01"].mean() / 1e5, 4), "[3M Avg (Lakh Cr)] at September 2026"],
    "fytd_sep_2026_cr": [round(m["2026-04-01":"2026-09-01"].sum()), "[FYTD (Cr)] at September 2026"],
    "fytd_aug_2025_yoy": [round(m["2025-04-01":"2025-08-01"].sum() / m["2024-04-01":"2024-08-01"].sum() - 1, 4), "[FYTD YoY %] at August 2025"],
    "igst_share_2025_26": [round(heads.loc["2025-26", "IGST"] / fy["2025-26"], 4), "IGST / all heads, FY 2025-26"],
    "sgst_share_2025_26": [round(heads.loc["2025-26", "SGST"] / fy["2025-26"], 4), "SGST / all heads, FY 2025-26"],
    "cgst_share_2025_26": [round(heads.loc["2025-26", "CGST"] / fy["2025-26"], 4), "CGST / all heads, FY 2025-26"],
}
out = {k: {"value": v, "how": how} for k, (v, how) in facts.items()}
with open("facts.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
for k, v in out.items():
    print(k, v["value"])
