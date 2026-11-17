# Part 4: Executive case study and desk-review QA

## Evidence
- Observed transaction evidence: UCI Online Retail II, 2009 to 2011. Sale lines exclude the repeated 1 to 9 Dec 2010 week, exact repeat lines, cancellations and nonpositive quantity or price. Product rankings are net of cancellations and exclude non-product codes.
- Classification audit: 4,917 stock codes, 591 queued for review.
- Desk-review validation: all 37 codes previously flagged as non-merchandise or requiring manual classification, using descriptions only. This cannot replace merchant product-master confirmation. 12 are likely physical products, demonstrating keyword false positives.
- Description review: 555 codes have multiple descriptions even after case/punctuation/whitespace normalization. This flags a review need, not 555 confirmed defects.
- Advertising model: all model inputs are hypothetical. ROAS and contribution figures are scenario outputs, not performance measurements or forecasts. The three budget tiers receive identical economics in each scenario; allocation is not optimized.
- Online-only retailer: zero observed station/store/offline evidence. Online-to-offline is outside measured scope.

## Reproducibility
Run `create_part4.py` with pandas and python-pptx after Part 3 outputs are in the same folder. It validates every scenario row and writes `part4_desk_review_37.csv`, `part4_scenario_validation.csv`, and the PowerPoint.

## Official references
- Google Merchant Center specifications: https://support.google.com/merchants/answer/7052112?hl=en
- 2027 image minimum: https://support.google.com/merchants/answer/16989427?hl=en

## Limitations
- Desk-review corrections are candidate labels, not proof of merchant eligibility.
- Manufacturer identifiers are conditional and must not be invented.
- No physical stores, ad data, visits, conversion attribution, or incremental lift can be measured from this source.
