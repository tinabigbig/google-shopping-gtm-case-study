"""Part 2 and 3: stock-code audit and illustrative Shopping budget scenarios.
Uses the shared cleaning rules in clean.py. Scenario inputs are assumptions, not observed ad results.
"""
import json, math, re, unicodedata
from collections import Counter
from decimal import Decimal as D
import pandas as pd
from clean import ROOT, load

OUT = ROOT / "data" / "processed"
CHARGE_CODES = {"M", "DOT", "POST", "BANK CHARGES", "AMAZONFEE", "D", "S", "C2", "CRUK", "ADJUST", "B", "PADS"}
CHARGE = re.compile(r"\b(?:POSTAGE|CARRIAGE|BANK CHARGES?|MANUAL|AMAZON FEE|DISCOUNT|ADJUSTMENT|CREDIT CARD CHARGE)\b", re.I)
AMBIG = re.compile(r"\b(?:SAMPLE|GIFT VOUCHER|GIFT CARD|TEST|CHARGES?|DAMAGED|CHECK|MISSING|WRONG|REPLACEMENT|RETURNED|LOST|CRUK)\b", re.I)


def normalize(s):
    s = unicodedata.normalize("NFKC", s).upper().replace("&", " AND ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", s)).strip()


counts, lines, sales, cancels = load()
sales["desc"] = sales["Description"].fillna("").str.strip()
cancelled = cancels.groupby("StockCode")["value"].sum()

rows, classes, class_sales, flags = [], Counter(), Counter(), Counter()
for code, g in sales.groupby("StockCode"):
    dc = Counter(g["desc"])
    desc = dc.most_common(1)[0][0]
    nonblank = [d for d in dc if d]
    nn = len({normalize(d) for d in nonblank})
    blank = dc.get("", 0)
    n_prices = g["Price"].nunique()
    if code.upper() in CHARGE_CODES or CHARGE.search(desc):
        cls, reason = "non_merchandise_candidate", "Charge or service-like code or description; confirm against the retailer product master"
    elif AMBIG.search(desc) or not desc or len(code) < 3:
        cls, reason = "manual_review", "Ambiguous text, missing title or short identifier"
    else:
        cls, reason = "merchandise_candidate", "Provisional, description-based; physical product not verified"
    review = []
    if len(nonblank) > 1 and nn == 1: review.append("formatting_only_variants"); flags["formatting_only_variants"] += 1
    if nn > 1: review.append("different_normalized_descriptions"); flags["different_normalized_descriptions"] += 1
    if len(nonblank) > 1: flags["multiple_raw_nonblank_descriptions"] += 1
    if blank: review.append("missing_description_observed"); flags["blank_description"] += 1
    if n_prices > 1: review.append("different_historical_prices_not_live_feed_conflict")
    if cls != "merchandise_candidate": review.append(cls)
    gross = g["value"].sum()
    classes[cls] += 1
    class_sales[cls] += gross
    rows.append({"stock_code": code, "representative_description": desc, "normalized_representative_description": normalize(desc),
                 "classification": cls, "classification_reason": reason,
                 "gross_sales_gbp": round(gross, 2), "net_sales_gbp": round(gross + cancelled.get(code, 0), 2),
                 "sale_lines": len(g), "distinct_nonblank_descriptions": len(nonblank), "distinct_normalized_descriptions": nn,
                 "blank_description_lines": blank, "distinct_historical_prices": n_prices, "review_flags": " | ".join(review),
                 "sample_alternative_descriptions": " || ".join([d for d, _ in dc.most_common(6) if d and d != desc][:4]),
                 "catalog_verification_status": "unverified"})

audit = pd.DataFrame(rows).sort_values("net_sales_gbp", ascending=False)
queue = audit[(audit.classification != "merchandise_candidate") | (audit.distinct_normalized_descriptions > 1) | (audit.blank_description_lines > 0)]
audit.to_csv(OUT / "full_stock_code_audit.csv", index=False)
queue.to_csv(OUT / "manual_review_queue.csv", index=False)

# Scenario model. Every media input is an assumption. AOV of £30 to £45 describes a CONSUMER launch,
# not the observed business, whose median order is about £300 from trade buyers.
eligible = audit[audit.classification == "merchandise_candidate"]
n = len(eligible)
bands = [("top_20pct", eligible.iloc[:math.ceil(n * .2)], "0.5"), ("middle_30pct", eligible.iloc[math.ceil(n * .2):math.ceil(n * .5)], "0.3"),
         ("remaining_50pct", eligible.iloc[math.ceil(n * .5):], "0.2")]
scenarios = [("low", "0.90", "0.01", "30", "0.35", "0.60"), ("base", "0.60", "0.025", "40", "0.45", "0.75"), ("high", "0.35", "0.04", "45", "0.50", "0.90")]
budget = D("10000")
models = []
for s, cpc, cvr, aov, gm, inc in scenarios:
    cpc, cvr, aov, gm, inc = map(D, (cpc, cvr, aov, gm, inc))
    for band, members, share in bands:
        spend = budget * D(share)
        clicks = spend / cpc
        orders = clicks * cvr
        rev = orders * aov
        contrib = rev * inc * gm - spend
        models.append({"scenario": s, "priority_band": band, "candidate_sku_count": len(members),
                       "historical_net_sales_gbp": round(members["net_sales_gbp"].sum(), 2),
                       "assumed_spend_gbp": str(spend), "assumed_cpc_gbp": str(cpc), "assumed_conversion_rate": str(cvr),
                       "assumed_order_value_gbp": str(aov), "assumed_gross_margin": str(gm), "assumed_incremental_share": str(inc),
                       "modeled_clicks": str(clicks.quantize(D(".01"))), "modeled_orders": str(orders.quantize(D(".01"))),
                       "modeled_ad_attributed_revenue_gbp": str(rev.quantize(D(".01"))), "modeled_roas": str((rev / spend).quantize(D(".001"))),
                       "modeled_incremental_contribution_after_ad_spend_gbp": str(contrib.quantize(D(".01"))),
                       "evidence_label": "HYPOTHETICAL consumer-launch scenario; historical sales only set the SKU tiers"})
pd.DataFrame(models).to_csv(OUT / "budget_scenarios.csv", index=False)

bycase = {}
for s, cpc, cvr, aov, gm, inc in scenarios:
    m = [r for r in models if r["scenario"] == s]
    total = sum(D(r["modeled_incremental_contribution_after_ad_spend_gbp"]) for r in m)
    exact = (budget / D(cpc) * D(cvr) * D(aov) * D(inc) * D(gm) - budget).quantize(D(".01"))
    assert abs(total - exact) <= D(".03")
    bycase[s] = {"spend_gbp": str(budget), "modeled_ad_attributed_revenue_gbp": str(sum(D(r["modeled_ad_attributed_revenue_gbp"]) for r in m)),
                 "modeled_incremental_contribution_after_ad_spend_gbp": str(total)}

assert sum(classes.values()) == len(audit)
assert abs(sum(class_sales.values()) - sales["value"].sum()) < 0.01
summary = {"source": "UCI Online Retail II; cleaned as in scripts/clean.py", "cleaning": counts,
           "sale_lines": len(sales), "stock_codes_full": len(audit), "gross_sale_line_value_gbp": round(sales["value"].sum(), 2),
           "provisional_class_counts": dict(classes), "provisional_class_gross_sales_gbp": {k: round(v, 2) for k, v in class_sales.items()},
           "description_flags": dict(flags), "review_queue_codes": len(queue),
           "top10_codes_by_net": audit.head(10)[["stock_code", "representative_description", "classification", "net_sales_gbp"]].to_dict("records"),
           "budget_scenarios": bycase,
           "cautions": ["A stock code is not a validated live catalog product; classifications need merchant review.",
                        "Historical prices are not current feed prices; no URLs, images, stock or verified identifiers.",
                        "No observed marketing spend, clicks, conversions, incrementality or offline journeys.",
                        "Scenario AOV of £30 to £45 describes a consumer launch; the observed median order is about £300 from trade buyers.",
                        "Modeled budget is illustrative, not a forecast or spend recommendation."]}
(OUT / "full_audit_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
print(json.dumps(summary, indent=2, default=str))
