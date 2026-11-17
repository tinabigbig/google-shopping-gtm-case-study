# Methodology and validation

## One row
One row is one product line on one invoice. All cleaning lives in `scripts/clean.py`, and every other script starts from it.

## Cleaning rules
| Step | Rows | Why |
|---|---|---|
| Raw rows, both sheets | 1,067,371 | |
| Remove 1 to 9 Dec 2010 from the second sheet | −22,523 | The first sheet already holds these days. Counting both double-counts a week. |
| Remove exact repeat lines | −11,812 | Every column identical, including timestamp. Treated as export repeats. |
| Clean rows | 1,033,036 | |
| Sale lines | 1,007,913 | Invoice not prefixed C, quantity > 0, price > 0, invoice and stock code present. |
| Cancellation lines | 19,104 | Invoice prefixed C. Used to net product value, never counted as sales. |

Gross sale-line value is £20,476,260.45, before £1,462,050.61 of cancellations. The first version of this project reported £20,972,594.57 because it kept the repeated week and the repeat lines (2.4% too high).

## Product ranking
Rankings use merchandise only, net of cancellations. Postage (`POST`, `DOT`), manual adjustments (`M`), fees, tests and gift vouchers are excluded from rankings but kept in totals (£832,413.56 of sale-line value). `PADS` stays in the ranking because the desk review found it is likely a real product. Netting matters: invoice 581483 sold 80,995 units of code 23843 for £168,469.60 and was cancelled in full twelve minutes later by C581484.

Top 10 merchandise codes make up 7.60% of merchandise net value (£18,927,648.20). The first version reported 10.28% because postage and fee codes were in the top 10.

## Who buys
Median order £302.22, mean £510.92, and 25.1% of sale lines are 12 or more units. The buyers are mostly trade customers placing wholesale-sized orders. 5,878 identified customers; 72.39% placed two or more orders. 228,488 sale lines have no customer ID and are left out of customer metrics.

## Product audit
Rules screen stock-code descriptions and normalize case, punctuation and whitespace. 4,917 stock codes; 623 have more than one raw description, 68 reduce to one after normalization, 555 keep more than one. 591 codes enter the review queue (reasons overlap). The 37 codes first labelled non-merchandise or ambiguous had a description-only desk review: 12 likely physical products, 24 likely non-merchandise or tests, 1 unresolved. A merchant product master is needed for ground truth.

## Offer and feed readiness
StockCode can seed an `id`, Description a draft `title`, and unit price only a historical price. A compliant offer still needs a verified landing page, image, current availability and current price; brand, GTIN and MPN depend on the product. No identifiers are invented. Google will enforce a 500 × 500 px minimum image size from 31 Jan 2027. Current specification: https://support.google.com/merchants/answer/7052112?hl=en

## Scenario model
£10,000 per scenario. Clicks = spend / CPC; orders = clicks × CVR; revenue = orders × AOV; ROAS = revenue / spend; contribution after ad spend = revenue × margin × incremental share − spend. Break-even ROAS = 1 / (margin × incremental share).

Every input is assumed. The £30 to £45 order values describe a new consumer audience, not the observed trade buyers (median order about £300). Inputs apply evenly across illustrative SKU tiers, so the tiers are not an optimized allocation. The results are illustrations, not forecasts.

## Validation
- `tests/independent_check.py` rebuilds the cleaning and the top-10 ranking with separate code.
- `tests/check_outputs.py` checks every output file against those figures and against each other: row counts at each cleaning step, gross value, invoices (40,077), stock codes, repeat rate, the top product, the absence of non-product codes and the cancelled order from the ranking, audit and queue counts, desk-review counts, and the three scenario results.
- Part 1 checks that product and invoice totals agree; Part 3 recomputes each scenario in closed form; Part 4 recomputes each scenario row.

## Limitations
No ads, stores, product feed, product master or attribution data. Historical and online only. Classifications are provisional.
