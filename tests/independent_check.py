# Independent check of the headline numbers, written separately from scripts/clean.py
#
# Goal: reproduce the headline figures from the raw workbook with separate code,
# and test two things the delivered scripts did not: the overlap between the two
# sheets, and orders that were cancelled in full.
#
# One row in the raw data = one product line on one invoice.

import pandas as pd

RAW = "data/processed/source.xlsx"
NON_PRODUCT_CODES = {"M", "DOT", "POST", "D", "C2", "BANK CHARGES", "AMAZONFEE", "ADJUST", "ADJUST2",
                     "CRUK", "S", "B", "TEST001", "TEST002", "SP1002", "gift_0001_10",
                     "gift_0001_20", "gift_0001_30", "gift_0001_40", "gift_0001_50"}

sheets = pd.read_excel(RAW, sheet_name=None, dtype={"Invoice": str, "StockCode": str})
for name, s in sheets.items():
    s["sheet"] = name
raw = pd.concat(sheets.values(), ignore_index=True)
line_cols = [c for c in raw.columns if c != "sheet"]


def qualifying(x):
    """The delivered rule: not a cancellation, quantity > 0, price > 0."""
    q = x[x["Invoice"].notna() & x["StockCode"].notna()
          & ~x["Invoice"].str.startswith("C") & (x["Quantity"] > 0) & (x["Price"] > 0)].copy()
    q["value"] = q["Quantity"] * q["Price"]
    return q


# Check 1: the two sheets overlap. 1 to 9 Dec 2010 appears in both.
for name, s in raw.groupby("sheet"):
    print(f"{name}: {s['InvoiceDate'].min()} to {s['InvoiceDate'].max()}")
in_both = raw[(raw["sheet"] == "Year 2010-2011") & (raw["InvoiceDate"] < "2010-12-10")]
print(f"Rows dated 1 to 9 Dec 2010 in the second sheet (also in the first): {len(in_both):,}")

no_overlap = raw.drop(in_both.index)
deduped = no_overlap[~no_overlap.duplicated(subset=line_cols)]
print(f"Exact repeated lines within a sheet after removing the overlap: {len(no_overlap) - len(deduped):,}")
print()

# Check 2: headline figures at each stage
for label, x in [("As delivered", raw), ("Overlap removed", no_overlap), ("Overlap and repeats removed", deduped)]:
    q = qualifying(x)
    print(f"{label:28s} lines {len(q):>9,}   positive line value £{q['value'].sum():>14,.2f}")
print()

# Check 3: top products. Delivered ranking includes non-products and orders cancelled in full.
q = qualifying(deduped)
cancels = deduped[deduped["Invoice"].str.startswith("C", na=False)].copy()
cancels["value"] = cancels["Quantity"] * cancels["Price"]          # negative

products = q[~q["StockCode"].isin(NON_PRODUCT_CODES)]
gross = products.groupby("StockCode")["value"].sum()
cancelled = cancels[~cancels["StockCode"].isin(NON_PRODUCT_CODES)].groupby("StockCode")["value"].sum()
net = gross.add(cancelled, fill_value=0)

names = q.groupby("StockCode")["Description"].first()
top = pd.DataFrame({"description": names, "gross": gross, "net_of_cancellations": net}).dropna(subset=["gross"])
top = top.sort_values("net_of_cancellations", ascending=False).head(10)
print("Top 10 merchandise codes, net of cancellations:")
print(top.round(2).to_string())
print()
print(f"Top 10 merchandise share of merchandise net value: {top['net_of_cancellations'].sum() / net.sum():.2%}")
