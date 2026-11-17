"""Check the outputs against figures reproduced by separate code (see tests/independent_check.py)
and against each other."""
from pathlib import Path
import csv, json, math

p = Path(__file__).resolve().parents[1] / "data" / "processed"
s = json.loads((p / "summary.json").read_text())
a = json.loads((p / "full_audit_summary.json").read_text())

# Cleaning: the sheet overlap and exact repeats are removed.
assert s["cleaning"] == a["cleaning"]
assert s["cleaning"]["raw_rows"] == 1067371
assert s["cleaning"]["overlap_rows_removed"] == 22523
assert s["cleaning"]["exact_repeat_rows_removed"] == 11812
assert s["sale_lines"] == a["sale_lines"] == 1007913

# Totals agree across scripts and with the independent check.
assert math.isclose(s["gross_sale_line_value_gbp"], 20476260.45, abs_tol=.01)
assert math.isclose(a["gross_sale_line_value_gbp"], s["gross_sale_line_value_gbp"], abs_tol=.01)
assert s["unique_stock_codes"] == a["stock_codes_full"] == 4917
assert s["unique_sale_invoices"] == 40077
assert s["repeat_customer_rate_percent"] == 72.39
assert s["top_10_merchandise_share_of_merchandise_net_percent"] == 7.60

# Top products are merchandise, net of cancellations.
with (p / "top_products.csv").open() as f:
    top = list(csv.DictReader(f))
assert top[0]["stock_code"] == "22423" and math.isclose(float(top[0]["net_sales_gbp"]), 314045.02, abs_tol=.01)
assert not {r["stock_code"] for r in top} & {"M", "DOT", "POST", "AMAZONFEE", "BANK CHARGES"}
assert "23843" not in {r["stock_code"] for r in top[:10]}   # 80,995-unit order cancelled in full

# Audit and review queue.
assert sum(a["provisional_class_counts"].values()) == 4917
with (p / "full_stock_code_audit.csv").open() as f: assert sum(1 for _ in csv.DictReader(f)) == 4917
with (p / "manual_review_queue.csv").open() as f: assert sum(1 for _ in csv.DictReader(f)) == 591
with (p / "part4_desk_review_37.csv").open() as f:
    r = list(csv.DictReader(f))
assert len(r) == 37 and sum(x["desk_review_class"] == "likely_physical_merchandise" for x in r) == 12

# Scenarios: break-even ROAS = 1 / (margin x incremental share).
with (p / "part4_scenario_validation.csv").open() as f:
    z = {r["scenario"]: r for r in csv.DictReader(f)}
for k, expected in [("low", -9300), ("base", -4375), ("high", 13142.86)]:
    assert math.isclose(float(z[k]["contribution_after_spend_gbp"]), expected, abs_tol=.01)
print("PASS: cleaning, totals, merchandise ranking, audit and scenarios")
