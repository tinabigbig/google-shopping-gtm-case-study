"""Part 1: product and customer profile.
Outputs: summary.json, top_products.csv, customer_segments.csv in data/processed.
"""
import json
import pandas as pd
from clean import ROOT, load

OUT = ROOT / "data" / "processed"
counts, lines, sales, cancels = load()

# Product ranking: merchandise only, net of cancellations.
prod = sales[sales["is_product"]]
gross = prod.groupby("StockCode").agg(sale_lines=("value", "size"), units=("Quantity", "sum"),
                                      gross_sales_gbp=("value", "sum"),
                                      description=("Description", lambda s: s.dropna().mode().iat[0] if s.notna().any() else ""))
cancelled = cancels[cancels["is_product"]].groupby("StockCode")["value"].sum()   # negative values
gross["cancelled_gbp"] = cancelled.reindex(gross.index).fillna(0)
gross["net_sales_gbp"] = gross["gross_sales_gbp"] + gross["cancelled_gbp"]
ranked = gross.sort_values("net_sales_gbp", ascending=False)
merch_net_total = ranked["net_sales_gbp"].sum()
ranked.head(100).round(2).reset_index().rename(columns={"StockCode": "stock_code"}).to_csv(OUT / "top_products.csv", index=False)

# Customers: identified only. Order = distinct sale invoice.
known = sales[sales["Customer ID"].notna()]
cust = known.groupby("Customer ID").agg(orders=("Invoice", "nunique"), sales_gbp=("value", "sum"))
seg = pd.cut(cust["orders"], [0, 1, 4, float("inf")], labels=["one_invoice", "two_to_four_invoices", "five_plus_invoices"])
segments = cust.groupby(seg, observed=False).agg(customer_count=("orders", "size"), customer_revenue_gbp=("sales_gbp", "sum"))
segments["customer_share_percent"] = (100 * segments["customer_count"] / len(cust)).round(2)
segments.round(2).reset_index(names="segment").to_csv(OUT / "customer_segments.csv", index=False)

# Order size: this tells us who the buyers are.
inv = sales.groupby("Invoice")["value"].sum()
total = sales["value"].sum()

summary = {
    "source": "UCI Online Retail II, both worksheets, UK online gift retailer, Dec 2009 to Dec 2011",
    "cleaning": counts,
    "measurement_scope": "Sale lines after removing the sheet overlap and exact repeats. Gross sale-line value is before cancellations; product rankings are net of cancellations and exclude non-product codes.",
    "sale_lines": len(sales),
    "unique_stock_codes": int(sales["StockCode"].nunique()),
    "unique_sale_invoices": int(sales["Invoice"].nunique()),
    "unique_identified_customers": len(cust),
    "repeat_customer_count_two_plus_invoices": int((cust["orders"] >= 2).sum()),
    "repeat_customer_rate_percent": round(100 * (cust["orders"] >= 2).mean(), 2),
    "gross_sale_line_value_gbp": round(total, 2),
    "independent_invoice_sum_gbp": round(inv.sum(), 2),
    "cancellation_value_gbp": round(cancels["value"].sum(), 2),
    "non_product_code_sales_gbp": round(sales.loc[~sales["is_product"], "value"].sum(), 2),
    "merchandise_net_of_cancellations_gbp": round(merch_net_total, 2),
    "top_10_merchandise_share_of_merchandise_net_percent": round(100 * ranked["net_sales_gbp"].head(10).sum() / merch_net_total, 2),
    "order_size": {
        "median_invoice_gbp": round(inv.median(), 2),
        "mean_invoice_gbp": round(inv.mean(), 2),
        "share_of_sale_lines_with_12_plus_units_percent": round(100 * (sales["Quantity"] >= 12).mean(), 2),
        "reading": "Mostly wholesale buyers placing trade-sized orders, not single consumer baskets.",
    },
    "sale_lines_by_year": {int(k): int(v) for k, v in sales["InvoiceDate"].dt.year.value_counts().sort_index().items()},
    "country_counts_top_5": [[k, int(v)] for k, v in sales["Country"].value_counts().head(5).items()],
    "valid_sale_lines_without_customer_id": int(sales["Customer ID"].isna().sum()),
    "limitations": [
        "Gross sale-line value is not net recognized revenue.",
        "Missing customer IDs are excluded from customer segmentation and repeat rate.",
        "Distinct invoices stand in for orders; no customer identity resolution.",
        "Stock codes and descriptions are not a Merchant Center feed.",
        "No ad spend, clicks, conversions, stores or offline journeys are observed.",
    ],
}
assert abs(summary["gross_sale_line_value_gbp"] - summary["independent_invoice_sum_gbp"]) < 0.01
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print(ranked.head(10)[["description", "gross_sales_gbp", "net_sales_gbp"]].round(2).to_string())
