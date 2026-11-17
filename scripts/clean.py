"""Shared loading and cleaning rules. Every other script starts here.

One row = one product line on one invoice.

Rules, in order:
1. Read both worksheets of data/processed/source.xlsx.
2. Drop the overlap: the second sheet repeats 1 to 9 Dec 2010, which the first sheet already holds.
3. Drop exact repeated lines (every column identical).
4. Sale lines: invoice not prefixed C, quantity > 0, price > 0, invoice and stock code present.
5. Cancellation lines: invoice prefixed C. Used to net product value, never counted as sales.
6. Non-product codes (postage, fees, manual adjustments, tests, vouchers) are kept in totals
   but excluded from product rankings.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "source.xlsx"
CACHE = ROOT / "data" / "interim" / "raw.pkl"
OVERLAP_SHEET, OVERLAP_END = "Year 2010-2011", "2010-12-10"

NON_PRODUCT_CODES = {"M", "m", "DOT", "POST", "D", "C2", "BANK CHARGES", "AMAZONFEE", "ADJUST", "ADJUST2",
                     "CRUK", "S", "B", "TEST001", "TEST002", "SP1002",
                     "gift_0001_10", "gift_0001_20", "gift_0001_30", "gift_0001_40", "gift_0001_50",
                     "gift_0001_70", "gift_0001_80"}


def load_raw():
    if CACHE.exists():
        return pd.read_pickle(CACHE)
    sheets = pd.read_excel(SOURCE, sheet_name=None, dtype={"Invoice": str, "StockCode": str, "Description": str})
    for name, s in sheets.items():
        s["sheet"] = name
    raw = pd.concat(sheets.values(), ignore_index=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    raw.to_pickle(CACHE)
    return raw


def load():
    """Return (counts, lines, sales, cancels)."""
    raw = load_raw()
    overlap = (raw["sheet"] == OVERLAP_SHEET) & (raw["InvoiceDate"] < OVERLAP_END)
    no_overlap = raw[~overlap]
    line_cols = [c for c in raw.columns if c != "sheet"]
    lines = no_overlap[~no_overlap.duplicated(subset=line_cols)].copy()
    lines["value"] = lines["Quantity"] * lines["Price"]

    present = lines["Invoice"].notna() & lines["StockCode"].notna() & (lines["StockCode"].str.strip() != "")
    is_cancel = lines["Invoice"].str.upper().str.startswith("C", na=False)
    sales = lines[present & ~is_cancel & (lines["Quantity"] > 0) & (lines["Price"] > 0)].copy()
    cancels = lines[present & is_cancel].copy()
    for df in (sales, cancels):
        df["is_product"] = ~df["StockCode"].isin(NON_PRODUCT_CODES)

    counts = {
        "raw_rows": len(raw),
        "overlap_rows_removed": int(overlap.sum()),
        "exact_repeat_rows_removed": len(no_overlap) - len(lines),
        "clean_rows": len(lines),
        "sale_lines": len(sales),
        "cancellation_lines": len(cancels),
    }
    return counts, lines, sales, cancels
