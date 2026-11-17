# Google Shopping GTM | Retail Feed Readiness & Commercial Scenario Analysis

**Independent portfolio case study** using UCI Online Retail II (2009 to 2011). Not an actual Google Ads account, retailer feed, or offline retail dataset.

## Executive outcome
A transaction export cannot safely serve as a live Google Shopping feed. Prioritize product identity, live offer attributes and measurement before spend. After removing a week both sheets repeat and exact repeat lines, the analysis covers 1,007,913 sale lines (£20.48M gross, before £1.46M of cancellations), 4,917 stock codes, a 591-code review queue and three explicitly hypothetical advertising scenarios. Today's buyers are mostly trade (median order £302), so the scenarios model a new consumer audience.

## Contents
- `scripts/clean.py`: shared loading and cleaning rules (sheet overlap, exact repeats, sale and cancellation lines, non-product codes).
- `scripts/analyze_part1.py`: product ranking (merchandise, net of cancellations), customer segments and order size.
- `scripts/audit_full_and_scenarios.py`: full stock-code classification, description normalization, queue and scenario model.
- `scripts/create_part4.py`: desk-review validation, scenario cross-check and executive presentation generation.
- `data/processed/`: source-derived summary tables and review candidates, not a verified merchant catalog.
- `docs/executive_deck.pptx`: five-slide commercial recommendations presentation.
- `docs/METHODOLOGY.md`: definitions, checks and limitations.

## Reproduce
1. Download the **UCI Online Retail II** dataset: https://archive.ics.uci.edu/dataset/502/online+retail+ii
2. Extract the two-sheet Excel workbook to `data/processed/source.xlsx` (file is deliberately omitted from the repository).
3. With Python 3.11+ install `pip install -r requirements.txt`.
4. From repository root run:
   ```bash
   python scripts/analyze_part1.py
   python scripts/audit_full_and_scenarios.py
   python scripts/create_part4.py
   python tests/check_outputs.py
   python tests/independent_check.py
   ```
5. The third script regenerates `docs/executive_deck.pptx`. The first run reads the workbook (about a minute) and caches it in `data/interim/`.

## Interpretation guardrails
- **Observed**: historical `Quantity × Price` sale-line values after de-duplication; product rankings net of cancellations; **not** recognized revenue.
- **Provisional**: merchandise/fee labels based on stock codes and descriptions; no live product-master confirmation.
- **Hypothetical**: advertising CPC, CVR, AOV, gross margin, incrementality, ROAS and contribution; no real Google Ads results.
- **Unsupported**: online-to-offline, store visits, omnichannel impact, inventory and feed approval.

Google Merchant Center product-data specification: https://support.google.com/merchants/answer/7052112?hl=en
