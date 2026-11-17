from pathlib import Path
import pandas as pd, json, csv, math, zipfile
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
p=Path(__file__).resolve().parents[1] / 'data' / 'processed'; d=pd.read_csv(p/'full_stock_code_audit.csv').fillna(''); scen=pd.read_csv(p/'budget_scenarios.csv');summary=json.loads((p/'full_audit_summary.json').read_text())
# Desk-review corrections: decisions are based on available descriptions, not retailer catalog verification.
merch={'23099','85168B','85168A','21347','PADS','21407','84795B','47367B','84795b','62043B','44091C','44091A'}
non={'M','DOT','POST','AMAZONFEE','C2','B','ADJUST','23444','ADJUST2','BANK CHARGES','D','S','m','gift_0001_30','gift_0001_20','gift_0001_50','gift_0001_40','gift_0001_10','gift_0001_80','gift_0001_70','TEST001','TEST002','23574','22016'}
# PADS is candidate physical accessory by description; low price is a data issue rather than proof of ineligibility.
uncertain={'85072'}
original=d[d.classification!='merchandise_candidate'].copy()
records=[]
for _,r in original.iterrows():
 code=r.stock_code
 revised='likely_physical_merchandise' if code in merch else 'likely_non_merchandise_or_test' if code in non else 'needs_catalog_confirmation'
 records.append({'stock_code':code,'description':r.representative_description,'initial_rule_class':r.classification,'desk_review_class':revised,'historical_net_sales_gbp':r.net_sales_gbp,'review_basis':'Description/code desk review only; merchant master and current eligibility unavailable','catalog_verified':'NO'})
review=pd.DataFrame(records);assert len(review)==37
review.to_csv(p/'part4_desk_review_37.csv',index=False)
# validate formulas independently
check=[]
for name,g in scen.groupby('scenario'):
 spend=float(g.assumed_spend_gbp.sum());rev=0;contrib=0
 for _,r in g.iterrows():
  clicks=r.assumed_spend_gbp/r.assumed_cpc_gbp;orders=clicks*r.assumed_conversion_rate;revenue=orders*r.assumed_order_value_gbp
  rev+=revenue;contrib+=revenue*r.assumed_gross_margin*r.assumed_incremental_share-r.assumed_spend_gbp
  assert abs(revenue-r.modeled_ad_attributed_revenue_gbp)<.03
  assert abs((revenue*r.assumed_gross_margin*r.assumed_incremental_share-r.assumed_spend_gbp)-r.modeled_incremental_contribution_after_ad_spend_gbp)<.03
 check.append({'scenario':name,'spend_gbp':spend,'modelled_revenue_gbp':round(rev,2),'contribution_after_spend_gbp':round(contrib,2),'break_even_roas_at_assumptions':round(1/(g.iloc[0].assumed_gross_margin*g.iloc[0].assumed_incremental_share),2)})
checks=pd.DataFrame(check);checks.to_csv(p/'part4_scenario_validation.csv',index=False)
# slides
prs=Presentation();prs.slide_width=Inches(13.33);prs.slide_height=Inches(7.5)
NAVY=RGBColor(22,42,65);TEAL=RGBColor(0,132,139);GRAY=RGBColor(85,100,112);PALE=RGBColor(235,245,247);WHITE=RGBColor(255,255,255)
def txt(s,x,y,w,h,size=18,bold=False,color=NAVY):
 tb=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=tb.text_frame;tf.word_wrap=True
 for i,line in enumerate(str(size and '').splitlines()):pass
 return tb
def text(s,content,x,y,w,h,size=18,bold=False,color=NAVY):
 shape=txt(s,x,y,w,h);tf=shape.text_frame;tf.clear();p=tf.paragraphs[0];p.text=content;p.font.name='Aptos';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color;return shape
def slide(title,kicker='GOOGLE SHOPPING GTM  /  INDEPENDENT CASE STUDY'):
 s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=WHITE
 text(s,kicker,.55,.25,12,.35,11,True,TEAL);text(s,title,.55,.82,12,1.0,30,True,NAVY)
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(.55),Inches(1.72),Inches(12.2),Inches(.035));sh.fill.solid();sh.fill.fore_color.rgb=TEAL;sh.line.fill.background()
 text(s,'UCI Online Retail II  •  Historical UK online-only retailer  •  Observed sales are not Google Ads outcomes',.55,7.09,12.2,.26,10,False,GRAY)
 return s
def bullet(s,content,x,y,w,size=17):
 text(s,'• '+content,x,y,w,.75,size,False,NAVY)
def panel(s,x,y,w,h,title,body):
 shape=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));shape.fill.solid();shape.fill.fore_color.rgb=PALE;shape.line.fill.background();text(s,title,x+.22,y+.15,w-.44,.4,17,True,TEAL);text(s,body,x+.22,y+.67,w-.44,h-.78,16)
# slide 1
s=slide('From retail transactions to Shopping readiness')
panel(s,.6,2.04,3.86,2.05,'1,007,913','Sale lines after removing a repeated week and exact repeat lines')
panel(s,4.72,2.04,3.86,2.05,'4,917','Stock codes sold')
panel(s,8.84,2.04,3.86,2.05,'£20.48M','Gross sale-line value before £1.46M of cancellations')
text(s,'Who buys today: mostly trade buyers. Median order £302; a quarter of lines are 12+ units.',.65,4.25,12,.45,16,False,GRAY)
text(s,'Executive decision',.65,4.75,5,.5,21,True,TEAL)
text(s,'Do not launch Shopping ads from this transaction extract. Establish merchandise identity and a current, validated product feed first.',.65,5.25,11.85,1.3,22,True,NAVY)
# slide 2
s=slide('The catalog audit exposes preventable GTM risks')
panel(s,.6,2.08,3.88,2.18,'591 flagged codes','Automated review queue; includes 555 with differing normalized descriptions')
panel(s,4.72,2.08,3.88,2.18,'37 desk-reviewed','All 18 initially labelled non-merchandise plus 19 uncertain codes')
panel(s,8.84,2.08,3.88,2.18,'12 likely physical goods','Flagged by charge/ambiguity keywords in initial rules')
bullet(s,'Examples: “FRENCH CARRIAGE LANTERN” and “BLACK BAROQUE CARRIAGE CLOCK” are likely physical goods.',.7,4.68,11.9,17)
bullet(s,'Code-level classifications remain provisional until checked against the merchant product master.',.7,5.58,11.9,17)
# slide 3
s=slide('Feed readiness: transaction fields are not live offers')
panel(s,.6,2.03,5.9,3.45,'Available, with limits','StockCode → candidate id\nDescription → candidate title\nHistorical price → not current offer price')
panel(s,6.75,2.03,5.9,3.45,'Missing or unverified','Product landing URLs and images\nLive inventory and current pricing\nBrand, GTIN/MPN where applicable\nOffer / landing-page consistency')
text(s,'2027 image change: Google will enforce a 500 × 500 px minimum from Jan 31, 2027. This is a future requirement, not a measured dataset defect.',.7,5.82,11.9,.85,15,False,GRAY)
# slide 4
s=slide('£10K consumer pilot: ROAS alone is not enough')
cols=[('LOW','0.33×','−£9,300','4.76× break-even ROAS'),('BASE','1.67×','−£4,375','2.96× break-even ROAS'),('HIGH','5.14×','+£13,143','2.22× break-even ROAS')]
for i,(name,roas,c,br) in enumerate(cols):
 x=.65+i*4.17;panel(s,x,2.10,3.85,3.25,name,f'ROAS {roas}\nContribution {c}\n{br}')
text(s,'All CPCs, conversion rates, order values, margins and incremental shares are assumptions; no Google Ads data exists here. The £30 to £45 order values model a new consumer audience, not today\'s trade buyers (median order £302).',.7,5.62,12,1.1,16,False,GRAY)
# slide 5
s=slide('Phased launch: invest in data readiness before media')
phases=[('P0','Identify sellable products','Remove fees / test codes; resolve uncertain stock-code identities'),('P0','Prepare compliant offers','Current price, availability, landing pages, images, required identifiers'),('P1','Validate & measure','Feed diagnostics, conversion tracking QA, deduplication, landing-page checks'),('P2','Small controlled pilot','Set spend cap; track incremental contribution and feed rejection rates')]
for i,(tag,title_,body) in enumerate(phases):
 y=1.96+i*1.07;text(s,tag,.75,y,.7,.5,17,True,TEAL);text(s,title_,1.65,y,4.1,.53,19,True,NAVY);text(s,body,5.6,y,6.75,.8,16)
text(s,'GO / NO-GO: No paid launch until critical feed fields are verified and tracking is tested. Scale only if incremental contribution is credible and improves against a control.',.7,6.38,12,.67,15,True,TEAL)
out=Path(__file__).resolve().parents[1] / 'docs' / 'executive_deck.pptx';prs.save(out)
readme='''# Part 4: Executive case study and desk-review QA\n\n## Evidence\n- Observed transaction evidence: UCI Online Retail II, 2009 to 2011. Sale lines exclude the repeated 1 to 9 Dec 2010 week, exact repeat lines, cancellations and nonpositive quantity or price. Product rankings are net of cancellations and exclude non-product codes.\n- Classification audit: 4,917 stock codes, 591 queued for review.\n- Desk-review validation: all 37 codes previously flagged as non-merchandise or requiring manual classification, using descriptions only. This cannot replace merchant product-master confirmation. 12 are likely physical products, demonstrating keyword false positives.\n- Description review: 555 codes have multiple descriptions even after case/punctuation/whitespace normalization. This flags a review need, not 555 confirmed defects.\n- Advertising model: all model inputs are hypothetical. ROAS and contribution figures are scenario outputs, not performance measurements or forecasts. The three budget tiers receive identical economics in each scenario; allocation is not optimized.\n- Online-only retailer: zero observed station/store/offline evidence. Online-to-offline is outside measured scope.\n\n## Reproducibility\nRun `create_part4.py` with pandas and python-pptx after Part 3 outputs are in the same folder. It validates every scenario row and writes `part4_desk_review_37.csv`, `part4_scenario_validation.csv`, and the PowerPoint.\n\n## Official references\n- Google Merchant Center specifications: https://support.google.com/merchants/answer/7052112?hl=en\n- 2027 image minimum: https://support.google.com/merchants/answer/16989427?hl=en\n\n## Limitations\n- Desk-review corrections are candidate labels, not proof of merchant eligibility.\n- Manufacturer identifiers are conditional and must not be invented.\n- No physical stores, ad data, visits, conversion attribution, or incremental lift can be measured from this source.\n'''
(p/'PART4_README.md').write_text(readme)
print('Saved', out)
