#!/usr/bin/env python3
"""Enrich quarterly BCTC snapshots from PDF/ZIP text already archived from VietstockFinance.

Only fills missing fields. Text/OCR-derived fields are marked pending visual review.
No prices, market multiples or other values are inferred from accounting reports.
"""
from __future__ import annotations
import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = ROOT / "reports" / "raw"
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])\(?-?\d[\d.,]*\d?\)?")
BANKS = {"MBB", "ACB", "SHB", "TCB"}
BROKERS = {"HCM", "SHS", "TCX", "VND"}
STANDARD_BUSINESSES = {"BSR", "FPT", "NLG", "VHM"}

BALANCE_LABELS = {
 "current_assets":["tai san ngan han"],
 "cash_and_equivalents":["tien va cac khoan tuong duong tien","tien va tuong duong tien","cash and cash equivalents"],
 "short_term_investments":["dau tu tai chinh ngan han"],
 "short_term_receivables":["cac khoan phai thu ngan han"],
 "inventory":["hang ton kho","inventories"],
 "non_current_assets":["tai san dai han"],
 "fixed_assets":["tai san co dinh"],
 "current_liabilities":["no phai tra ngan han","no ngan han"],
 "long_term_liabilities":["no phai tra dai han","no dai han"],
 "retained_earnings":["loi nhuan sau thue chua phan phoi","loi nhuan chua phan phoi"],
}
INCOME_LABELS = {
 "cost_of_goods_sold":["gia von hang ban"],
 "gross_profit":["loi nhuan gop ve ban hang va cung cap dich vu","loi nhuan gop"],
 "financial_income":["doanh thu hoat dong tai chinh"],
 "financial_expense":["chi phi tai chinh"],
 "interest_expense":["chi phi lai vay","chi phi di vay","chi phi lai va cac khoan chi phi tuong tu"],
 "selling_expense":["chi phi ban hang"],
 "admin_expense":["chi phi quan ly doanh nghiep","chi phi quan ly cong ty"],
 "operating_profit":["loi nhuan thuan tu hoat dong kinh doanh","loi nhuan tu hoat dong kinh doanh"],
 "income_tax":["chi phi thue thu nhap doanh nghiep trong ky","chi phi thue thu nhap doanh nghiep","chi phi thue tndn"],
 "net_profit_attributable":["loi nhuan sau thue cua co dong cong ty me","loi nhuan sau thue cua co dong cua cong ty me","loi nhuan thuoc ve co dong cong ty me"],
}
CASHFLOW_LABELS = {
 "operating_cash_flow_ytd":["luu chuyen tien thuan tu hoat dong kinh doanh","luu chuyen tien tu hoat dong kinh doanh"],
 "investing_cash_flow_ytd":["luu chuyen tien thuan tu hoat dong dau tu","luu chuyen tien tu hoat dong dau tu"],
 "financing_cash_flow_ytd":["luu chuyen tien thuan tu hoat dong tai chinh","luu chuyen tien tu hoat dong tai chinh"],
 "capital_expenditure_ytd":["tien chi de mua sam xay dung tai san co dinh","tien chi mua sam xay dung tai san co dinh","mua sam xay dung tai san co dinh va cac tai san dai han khac"],
 "dividends_paid_ytd":["co tuc loi nhuan da tra cho chu so huu","tien chi tra co tuc loi nhuan cho chu so huu"],
 "net_cash_change_ytd":["luu chuyen tien thuan trong ky","luu chuyen tien thuan trong nam"],
 "cash_beginning":["tien va cac khoan tuong duong tien dau ky","tien va tuong duong tien dau ky"],
 "cash_ending":["tien va cac khoan tuong duong tien cuoi ky","tien va tuong duong tien cuoi ky"],
 "foreign_exchange_effect_ytd":["anh huong cua thay doi ty gia hoi doai quy doi ngoai te","anh huong thay doi ty gia hoi doai"],
}
BALANCE_CODES = {
 "current_assets":"100","cash_and_equivalents":"110","short_term_investments":"120",
 "short_term_receivables":"130","inventory":"140","non_current_assets":"200",
 "fixed_assets":"220","current_liabilities":"310","long_term_liabilities":"330",
 "retained_earnings":"421",
}
INCOME_CODES = {
 "revenue":"10","cost_of_goods_sold":"11","gross_profit":"20","financial_income":"21",
 "financial_expense":"22","interest_expense":"23","selling_expense":"25",
 "admin_expense":"26","operating_profit":"30","income_tax":"51","net_profit_attributable":"61",
}
CASHFLOW_CODES = {
 "operating_cash_flow_ytd":"20","capital_expenditure_ytd":"21",
 "investing_cash_flow_ytd":"30","dividends_paid_ytd":"35",
 "financing_cash_flow_ytd":"40","net_cash_change_ytd":"50",
 "cash_beginning":"60","cash_ending":"70",
}
CASHFLOW_QUARTER_FROM_YTD = {
 "operating_cash_flow":"operating_cash_flow_ytd",
 "investing_cash_flow":"investing_cash_flow_ytd",
 "financing_cash_flow":"financing_cash_flow_ytd",
 "capital_expenditure":"capital_expenditure_ytd",
 "dividends_paid":"dividends_paid_ytd",
 "net_cash_change":"net_cash_change_ytd",
 "foreign_exchange_effect":"foreign_exchange_effect_ytd",
}

def norm(v):
 s=str(v or "").lower().replace("đ","d")
 s=unicodedata.normalize("NFD",s)
 s="".join(ch for ch in s if unicodedata.category(ch)!="Mn")
 return re.sub(r"\s+"," ",s).strip()

def parse_amount(token):
 raw=token.strip().replace(" ","")
 if not raw: return None
 neg=raw.startswith("(") or raw.startswith("-")
 raw=raw.strip("()").lstrip("+-").replace(".","").replace(",","")
 if not raw.isdigit(): return None
 value=int(raw)
 return -value if neg else value

def amounts(line, threshold=1000):
 # Do not allow spaces inside a number token: that would concatenate separate
 # reporting-period columns into a gigantic false value.
 vals=[]
 for token in NUMBER_RE.findall(line):
  n=parse_amount(token)
  if n is not None and abs(n)>=threshold and not (1900 <= abs(n) <= 2100):
   vals.append(n)
 return vals

def get_pages(obj):
 raw=obj.get("pages")
 return [p for p in raw if isinstance(p,dict) and p.get("text")] if isinstance(raw,list) else []

def select_statement_pages(pages,kind):
 terms={
  "balance":["bao cao tinh hinh tai chinh","bang can doi ke toan","statement of financial position"],
  "income":["bao cao ket qua hoat dong","bao cao ket qua kinh doanh","bao cao thu nhap","statement of income","income statement"],
  "cashflow":["bao cao luu chuyen tien te","luu chuyen tien te","statement of cash flows","cash flow statement"],
 }[kind]
 selected=[]
 for page in pages:
  text=norm(page.get("text",""))
  if "muc luc" in text or "table of contents" in text or "thuyet minh bao cao tai chinh" in text or "notes to the financial statements" in text:
   continue
  if any(term in text for term in terms):
   selected.append(page)
 return selected

def unit_factor(pages,item):
 header=norm(" ".join(str(p.get("text",""))[:5000] for p in pages[:3]))
 if any(t in header for t in ("nghin dong","nghin vnd","thousand vnd")): return 0.001
 if any(t in header for t in ("trieu dong","trieu vnd","million vnd")): return 1.0
 if any(t in header for t in ("ty dong","ty vnd","billion vnd")): return 1000.0
 if re.search(r"\bvnd\b",header) or "don vi tinh dong" in header: return 0.000001
 unit=norm(item.get("unit",""))
 if "trieu" in unit or "million" in unit: return 1.0
 if "nghin" in unit or "thousand" in unit: return 0.001
 if re.search(r"\bty\b",unit) or "billion" in unit: return 1000.0
 return 1.0

def is_statement_row_start(line):
 # Interim PDFs often wrap an item label across lines. A new row generally
 # starts with a short account code followed by a pipe or another code.
 return bool(re.match(r"^\s*(?:\|\s*)?\d{1,3}\s*(?:\||\s+\d{1,3}\s)",str(line or "")))

def value_by_label(pages,labels,factor,threshold=1000):
 for label in labels:
  target=norm(label)
  for page in pages:
   lines=str(page.get("text","")).splitlines()
   for start in range(len(lines)):
    parts=[]
    for end in range(start,min(start+4,len(lines))):
     if end>start and is_statement_row_start(lines[end]): break
     parts.append(lines[end])
     combined=norm(" ".join(parts))
     position=combined.find(target)
     if position < 0: continue
     # Search after the complete label, including wrapped continuation lines.
     tail=combined[position+len(target):]
     vals=amounts(tail,threshold=threshold)
     if vals: return int(round(vals[0]*factor))
 return None

def value_by_code(pages,code,factor):
 token=re.compile(r"(?<!\d)"+re.escape(code)+r"(?!\d)")
 for page in pages:
  for line in str(page.get("text","")).splitlines():
   matches=list(token.finditer(line))
   for match in reversed(matches):
    vals=[n for n in amounts(line[match.end():]) if abs(n)>=1000]
    if vals: return int(round(vals[0]*factor))
 return None

def load_report_pages(item,symbol):
 source=str(item.get("source_archive_file") or "").strip()
 if not source: return []
 file=(ROOT/source).resolve()
 try: file.relative_to(RAW.resolve())
 except ValueError: return []
 extracted=file.with_suffix(file.suffix+".extracted.json")
 if not extracted.is_file(): return []
 try: payload=json.loads(extracted.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError): return []
 candidates=[]
 members=payload.get("members")
 if isinstance(members,list):
  preferred=str(item.get("source_archive_member") or item.get("source_member_name") or item.get("source_extracted_file") or "").replace("\\","/").lower()
  consolidated=("hop nhat" in norm(item.get("report_type","")) or "consolidated" in norm(item.get("report_type","")))
  for member in members:
   if not isinstance(member,dict) or member.get("kind")!="pdf": continue
   pages=get_pages(member)
   if not pages: continue
   name=str(member.get("name") or "").replace("\\","/")
   nn=norm(name)
   texts=norm(" ".join(str(p.get("text",""))[:1500] for p in pages[:10]))
   score=min(len(pages),10)
   if preferred and name.lower()==preferred: score+=100
   elif preferred and name.lower().endswith(preferred): score+=90
   if consolidated and any(t in nn for t in ("hop nhat","hopnhat","consolidated")): score+=30
   if not consolidated and any(t in nn for t in ("rieng le","rieng","congtyme")): score+=20
   if symbol.lower() in nn: score+=5
   if "bao cao tai chinh" in texts or "financial statement" in texts: score+=2
   candidates.append((score,pages))
 direct=get_pages(payload)
 if direct:
  direct_text=norm(" ".join(str(p.get("text",""))[:1000] for p in direct[:10]))
  score=min(len(direct),10)+(2 if "bao cao tai chinh" in direct_text or "financial statement" in direct_text else 0)
  candidates.append((score,direct))
 if not candidates: return []
 candidates.sort(key=lambda pair:pair[0],reverse=True)
 return candidates[0][1]

def extract_fields(item,symbol,pages):
 bal=select_statement_pages(pages,"balance")
 inc=select_statement_pages(pages,"income")
 cf=select_statement_pages(pages,"cashflow")
 if not bal and not inc and not cf: return {}
 scale=unit_factor(bal or inc or cf,item)
 out={}
 for field,labels in BALANCE_LABELS.items():
  val=value_by_label(bal,labels,scale) if bal else None
  if val is None and symbol in STANDARD_BUSINESSES and bal: val=value_by_code(bal,BALANCE_CODES[field],scale)
  if val is not None: out[field]=val
 if symbol in BANKS:
  revlabels=["tong thu nhap hoat dong","tong thu nhap hoat dong kinh doanh","doanh thu hoat dong","thu nhap lai thuan"]
 elif symbol in BROKERS:
  revlabels=["doanh thu hoat dong","tong doanh thu hoat dong kinh doanh","doanh thu thuan"]
 else:
  revlabels=["doanh thu thuan ve ban hang va cung cap dich vu","doanh thu thuan","doanh thu ban hang va cung cap dich vu"]
 revenue=value_by_label(inc,revlabels,scale) if inc else None
 if revenue is None and symbol in STANDARD_BUSINESSES and inc: revenue=value_by_code(inc,INCOME_CODES["revenue"],scale)
 if revenue is not None: out["revenue"]=revenue
 for field,labels in INCOME_LABELS.items():
  if field=="income_tax": continue
  val=value_by_label(inc,labels,scale) if inc else None
  if val is None and symbol in STANDARD_BUSINESSES and inc and field in INCOME_CODES:
   val=value_by_code(inc,INCOME_CODES[field],scale)
  if val is not None: out[field]=val

 # Preserve current and deferred tax separately, then calculate the total tax
 # expense/income only from the values reported in the same statement.
 tax_current=value_by_label(inc,["chi phi thue tndn hien hanh","chi phi thue thu nhap doanh nghiep hien hanh"],scale) if inc else None
 tax_deferred=value_by_label(inc,["chi phi thue tndn hoan lai","chi phi thue thu nhap doanh nghiep hoan lai"],scale) if inc else None
 if tax_current is not None: out["income_tax_current"]=tax_current
 if tax_deferred is not None: out["income_tax_deferred"]=tax_deferred
 if tax_current is not None or tax_deferred is not None:
  out["income_tax"]=(tax_current or 0)+(tax_deferred or 0)
 else:
  tax_total=value_by_label(inc,INCOME_LABELS["income_tax"],scale) if inc else None
  if tax_total is None and symbol in STANDARD_BUSINESSES and inc:
   tax_total=value_by_code(inc,INCOME_CODES["income_tax"],scale)
  if tax_total is not None: out["income_tax"]=tax_total
 # Cash-flow rows are normally cumulative from 1 January on Q2/Q3/annual filings.
 for field,labels in CASHFLOW_LABELS.items():
  val=value_by_label(cf,labels,scale) if cf else None
  if val is None and symbol in STANDARD_BUSINESSES and cf: val=value_by_code(cf,CASHFLOW_CODES[field],scale)
  if val is not None: out[field]=val
 if symbol in STANDARD_BUSINESSES and inc:
  basic_eps=value_by_code(inc,"70",1.0)
  diluted_eps=value_by_code(inc,"71",1.0)
  if basic_eps is not None and abs(basic_eps)<1000000: out["eps"]=basic_eps
  if diluted_eps is not None and abs(diluted_eps)<1000000: out["diluted_eps"]=diluted_eps
 if cf:
  cft=norm(" ".join(str(p.get("text","")) for p in cf))
  is_ytd=bool(re.search(r"\b01\s*/\s*01\s*/?\s*20\d{2}\b",cft) or "tu ngay 01 thang 01" in cft or "luy ke tu dau nam" in cft or "giai doan tu 01/01" in cft)
  out["__cashflow_period_basis"]="year_to_date" if is_ytd else "quarterly_reported"
 return out

def period_key(item):
 m=re.fullmatch(r"(20\d{2})-Q([1-4])",str(item.get("period","")))
 return (int(m.group(1)),int(m.group(2))) if m else None

def sane_fields(item, found, symbol):
 # Cross-check extracted values against reconciled financial-statement totals.
 assets=item.get("total_assets")
 liabilities=item.get("total_liabilities")
 equity=item.get("equity")
 has_assets=isinstance(assets,(int,float)) and assets>0
 has_liabilities=isinstance(liabilities,(int,float)) and liabilities>=0
 has_equity=isinstance(equity,(int,float)) and equity>=0
 asset_fields={"current_assets","cash_and_equivalents","short_term_investments","short_term_receivables","inventory","non_current_assets","fixed_assets"}
 liability_fields={"current_liabilities","long_term_liabilities"}
 retained_fields={"retained_earnings"}
 income_fields={"revenue","cost_of_goods_sold","gross_profit","financial_income","financial_expense","interest_expense","selling_expense","admin_expense","operating_profit","income_tax","income_tax_current","income_tax_deferred","net_profit_attributable"}
 cash_fields=set(CASHFLOW_LABELS)-{"cash_beginning","cash_ending"}
 safe={}
 rejected=[]
 def discard(*fields,reason):
  for field in fields:
   if field in safe:
    safe.pop(field,None)
    rejected.append(field+"_"+reason)
 def value(field):
  candidate=safe.get(field)
  if isinstance(candidate,(int,float)): return candidate
  existing=item.get(field)
  return existing if isinstance(existing,(int,float)) else None
 for field,candidate in found.items():
  if field.startswith("__"):
   safe[field]=candidate
   continue
  if not isinstance(candidate,(int,float)) or not __import__("math").isfinite(candidate):
   rejected.append(field); continue
  limit=None
  if field in asset_fields and has_assets: limit=max(abs(assets)*1.25,1000)
  elif field in liability_fields and has_liabilities: limit=max(abs(liabilities)*1.25,1000)
  elif field in retained_fields and has_equity: limit=max(abs(equity)*1.75,1000)
  elif field in income_fields and has_assets: limit=max(abs(assets)*5,1000)
  elif field in cash_fields and has_assets: limit=max(abs(assets)*5,1000)
  elif field in {"cash_beginning","cash_ending"} and has_assets: limit=max(abs(assets)*1.5,1000)
  if limit is not None and abs(candidate)>limit:
   rejected.append(field+"_magnitude"); continue
  safe[field]=candidate

 # A tiny 'current-assets' subtotal is usually a wrapped-label false match in
 # bank/other statements; do not accept a subtotal below 0.5% of total assets.
 ca=value("current_assets")
 if has_assets and ca is not None and abs(ca)<abs(assets)*0.005:
  discard("current_assets",reason="current_assets_too_small")

 ca=value("current_assets")
 nca=value("non_current_assets")
 if has_assets and ca is not None and nca is not None:
  if abs(ca+nca-assets)>max(abs(assets)*0.08,1000):
   discard("current_assets","non_current_assets",reason="asset_total_check")

 cl=value("current_liabilities")
 ll=value("long_term_liabilities")
 if has_liabilities and cl is not None and ll is not None:
  if abs(cl+ll-liabilities)>max(abs(liabilities)*0.08,1000):
   discard("current_liabilities","long_term_liabilities",reason="liability_total_check")

 ca=value("current_assets")
 if ca is not None and ca>0:
  for field in ("cash_and_equivalents","short_term_investments","short_term_receivables","inventory"):
   part=value(field)
   if part is not None and abs(part)>max(abs(ca)*1.25,1000):
    discard(field,reason="current_asset_component_check")
 nca=value("non_current_assets")
 fa=value("fixed_assets")
 if nca is not None and nca>0 and fa is not None:
  if abs(fa)>max(abs(nca)*1.25,1000):
   discard("fixed_assets",reason="fixed_asset_parent_check")

 if symbol in STANDARD_BUSINESSES:
  rev=value("revenue")
  cogs=value("cost_of_goods_sold")
  gross=value("gross_profit")
  if rev is not None and cogs is not None and gross is not None:
   expected=rev-abs(cogs)
   tolerance=max(abs(rev)*0.03,1000)
   if abs(expected-gross)>tolerance:
    discard("revenue","cost_of_goods_sold","gross_profit",reason="gross_profit_equation_check")
  rev=value("revenue")
  finance_income=value("financial_income")
  if rev is not None and rev>0 and finance_income is not None and abs(finance_income)>abs(rev)*0.5:
   discard("financial_income",reason="finance_income_ratio_check")

 # Tax should reconcile to the absolute gap between pre-tax and after-tax profit.
 # Signed tax components are kept exactly as printed in the PDF; only the
 # magnitude is compared because statement sign conventions differ by issuer.
 pbt=item.get("pretax_profit")
 net=item.get("net_profit")
 tax=value("income_tax")
 if isinstance(pbt,(int,float)) and isinstance(net,(int,float)) and tax is not None:
  tax_gap=abs(pbt-net)
  if tax_gap>1000 and abs(abs(tax)-tax_gap)>max(tax_gap*0.25,1000):
   discard("income_tax","income_tax_current","income_tax_deferred",reason="tax_reconciliation_check")
 return safe,rejected

def reconcile_detail_items(items,symbol):
 changed=False
 affected_quarters=0
 changed_fields=0
 for item in items:
  if not isinstance(item,dict) or not item.get("financial_line_items_status"):
   continue
  period_changed=False
  fields=set(item.get("financial_line_items_extracted_fields") or [])
  rejected=set(item.get("financial_line_items_rejected_fields") or [])
  notes=[]
  prior=item.setdefault("financial_line_items_prior_values",{})
  rejected_values=item.setdefault("financial_line_items_rejected_values",{})

  # Net revenue = gross profit + absolute cost of goods sold. If OCR garbles
  # the revenue digit(s), reconstruct from the two corresponding statement
  # rows and record the derivation instead of retaining a conflicting value.
  if symbol in STANDARD_BUSINESSES:
   rev=item.get("revenue")
   cogs=item.get("cost_of_goods_sold")
   gross=item.get("gross_profit")
   if isinstance(cogs,(int,float)) and isinstance(gross,(int,float)):
    reconstructed=int(round(gross+abs(cogs)))
    if reconstructed>0 and isinstance(rev,(int,float)) and abs(rev-reconstructed)>max(abs(reconstructed)*0.003,1000):
     prior.setdefault("revenue",rev)
     item["revenue"]=reconstructed
     item["revenue_calculation"]="Lợi nhuận gộp + |giá vốn hàng bán|; tái lập từ hai dòng của BCTC do doanh thu OCR không khớp."
     item["financial_line_items_revenue_reconciliation"]={
      "previous_value":rev,"reconstructed_value":reconstructed,
      "formula":"gross_profit + abs(cost_of_goods_sold)",
      "difference_from_parsed_value":int(round(rev-reconstructed))
     }
     fields.add("revenue")
     notes.append("Doanh thu được tái lập từ lợi nhuận gộp và giá vốn do số OCR không khớp; cần đối chiếu trực quan.")
     period_changed=True; changed_fields+=1

  # PBT less after-tax profit is a reliable total-tax cross-check when both
  # profit totals are available in the same quarterly snapshot.
  pbt=item.get("pretax_profit")
  net=item.get("net_profit")
  tax=item.get("income_tax")
  if isinstance(pbt,(int,float)) and isinstance(net,(int,float)):
   expected_tax=int(round(pbt-net))
   if expected_tax!=0 and (not isinstance(tax,(int,float)) or abs(tax-expected_tax)>max(abs(expected_tax)*0.02,1000)):
    if isinstance(tax,(int,float)):
     prior.setdefault("income_tax",tax)
    item["income_tax"]=expected_tax
    item["income_tax_calculation"]="Lợi nhuận trước thuế - lợi nhuận sau thuế; chỉ dùng khi hai tổng lợi nhuận của cùng kỳ đã có."
    fields.add("income_tax")
    notes.append("Tổng thuế được đối chiếu từ lợi nhuận trước thuế trừ lợi nhuận sau thuế.")
    period_changed=True; changed_fields+=1

  def reject(*keys,reason):
   nonlocal period_changed,changed_fields
   for key in keys:
    if key in item and isinstance(item.get(key),(int,float)):
     rejected_values.setdefault(key,{"value":item[key],"reason":reason})
     item.pop(key,None)
     rejected.add(key)
     fields.discard(key)
     period_changed=True; changed_fields+=1

  # A row-by-row cash-flow sum should reconcile to net change once the FX line
  # is included. If not, leave those automatically parsed flow fields blank.
  operating=item.get("operating_cash_flow")
  investing=item.get("investing_cash_flow")
  financing=item.get("financing_cash_flow")
  net_change=item.get("net_cash_change")
  fx=item.get("foreign_exchange_effect",0)
  if all(isinstance(v,(int,float)) for v in (operating,investing,financing,net_change)) and isinstance(fx,(int,float)):
   total=operating+investing+financing+fx
   scale=max(abs(operating)+abs(investing)+abs(financing)+abs(fx),abs(net_change),1000)
   if abs(total-net_change)>max(scale*0.05,1000):
    reject("operating_cash_flow","investing_cash_flow","financing_cash_flow","foreign_exchange_effect",
           "net_cash_change","capital_expenditure","dividends_paid",
           "operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd",
           "foreign_exchange_effect_ytd","net_cash_change_ytd","capital_expenditure_ytd",
           "dividends_paid_ytd","cash_beginning","cash_ending",
           reason="cash-flow components do not reconcile to reported net cash change")
    notes.append("Dòng tiền tự trích xuất bị ẩn vì tổng các luồng tiền không khớp biến động tiền thuần.")

  # Validate balance-sheet subtotal equations against the original reconciled snapshot.
  assets=item.get("total_assets")
  liabilities=item.get("total_liabilities")
  ca=item.get("current_assets")
  nca=item.get("non_current_assets")
  cl=item.get("current_liabilities")
  ll=item.get("long_term_liabilities")
  if isinstance(assets,(int,float)) and isinstance(ca,(int,float)) and isinstance(nca,(int,float)):
   if abs(ca+nca-assets)>max(abs(assets)*0.08,1000):
    reject("current_assets","non_current_assets",reason="asset subtotals do not reconcile")
    notes.append("Tài sản ngắn hạn/dài hạn bị ẩn do tổng không khớp tổng tài sản.")
  if isinstance(liabilities,(int,float)) and isinstance(cl,(int,float)) and isinstance(ll,(int,float)):
   if abs(cl+ll-liabilities)>max(abs(liabilities)*0.08,1000):
    reject("current_liabilities","long_term_liabilities",reason="liability subtotals do not reconcile")
    notes.append("Nợ ngắn hạn/dài hạn bị ẩn do tổng không khớp nợ phải trả.")

  ca=item.get("current_assets")
  if isinstance(ca,(int,float)) and ca>0:
   for key in ("cash_and_equivalents","short_term_investments","short_term_receivables","inventory"):
    part=item.get(key)
    if isinstance(part,(int,float)) and abs(part)>max(abs(ca)*1.25,1000):
     reject(key,reason="asset component exceeds current assets")
  nca=item.get("non_current_assets")
  fixed=item.get("fixed_assets")
  if isinstance(nca,(int,float)) and nca>0 and isinstance(fixed,(int,float)) and abs(fixed)>max(abs(nca)*1.25,1000):
   reject("fixed_assets",reason="fixed assets exceed non-current assets")

  # Beginning/ending cash must reconcile to standalone-quarter net cash change.
  begin=item.get("cash_beginning")
  end=item.get("cash_ending")
  net_change=item.get("net_cash_change")
  if all(isinstance(v,(int,float)) for v in (begin,end,net_change)):
   tolerance=max(5,abs(begin)*0.0005,abs(end)*0.0005)
   if abs((end-begin)-net_change)>tolerance:
    reject("cash_beginning","cash_ending",reason="cash balance bridge does not reconcile to net cash change")
    notes.append("Số dư tiền đầu/cuối kỳ bị ẩn vì không khớp biến động tiền thuần theo quý.")

  if rejected:
   item["financial_line_items_rejected_fields"]=sorted(rejected)
   fields.difference_update(rejected)
  if fields!=set(item.get("financial_line_items_extracted_fields") or []):
   item["financial_line_items_extracted_fields"]=sorted(fields)
   period_changed=True
  if notes:
   current_note=str(item.get("financial_line_items_note") or "")
   addition=" ".join(dict.fromkeys(notes))
   if addition not in current_note:
    item["financial_line_items_note"]=(current_note+" "+addition).strip()
    period_changed=True
  if period_changed:
   item["financial_line_items_status"]="auto_extracted_pending_visual_review"
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True; affected_quarters+=1
 return changed,affected_quarters,changed_fields


def enrich_snapshot(path):
 snapshot=json.loads(path.read_text(encoding="utf-8"))
 symbol=str(snapshot.get("symbol") or path.stem.replace("financials-","")).upper()
 items=snapshot.get("items")
 if not isinstance(items,list): return False,0,0
 changed=False; quarter_count=0; field_count=0
 for item in items:
  if not isinstance(item,dict) or not period_key(item): continue
  pages=load_report_pages(item,symbol)
  if not pages: continue
  found=extract_fields(item,symbol,pages)
  if not found: continue
  suppressed=set(item.get("financial_line_items_rejected_fields") or [])
  for key in list(found):
   if not key.startswith("__") and key in suppressed:
    found.pop(key,None)
  if not found: continue
  found,rejected=sane_fields(item,found,symbol)
  if rejected:
   print(f"{path.name if 'path' in locals() else symbol} {item.get('period')}: skipped implausible extracted values {','.join(rejected)}")
  if not found: continue
  new_fields=[]
  for field,value in found.items():
   if field.startswith("__"): continue
   if item.get(field) is None:
    item[field]=value; new_fields.append(field)
   elif field=="revenue" and symbol in STANDARD_BUSINESSES and isinstance(item.get("revenue"),(int,float)):
    # Override a legacy revenue value only when the newly parsed row is backed
    # by matching revenue/COGS/gross-profit arithmetic.
    cogs=found.get("cost_of_goods_sold",item.get("cost_of_goods_sold"))
    gross=found.get("gross_profit",item.get("gross_profit"))
    consistent=(isinstance(cogs,(int,float)) and isinstance(gross,(int,float))
      and abs((value-abs(cogs))-gross)<=max(abs(value)*0.03,1000))
    if consistent and abs(value-item["revenue"])>max(abs(value)*0.02,1000):
     item.setdefault("financial_line_items_prior_values",{})["revenue"]=item["revenue"]
     item.setdefault("financial_line_items_overrides",{})["revenue"]={
      "previous_value":item["revenue"],"new_value":value,
      "reason":"Dòng doanh thu thuần trong báo cáo gốc khớp với giá vốn và lợi nhuận gộp."
     }
     item["revenue"]=value
     new_fields.append("revenue")
  basis=found.get("__cashflow_period_basis")
  if basis and item.get("cashflow_period_basis")!=basis:
   item["cashflow_period_basis"]=basis; new_fields.append("cashflow_period_basis")
  if new_fields:
   fields=set(item.get("financial_line_items_extracted_fields") or [])
   fields.update(new_fields)
   item["financial_line_items_extracted_fields"]=sorted(fields)
   item["financial_line_items_status"]="auto_extracted_pending_visual_review"
   item["financial_line_items_source"]=str(item.get("source_archive_file") or "")
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   item["financial_line_items_note"]="Trích xuất từ văn bản PDF/ZIP đã lưu; cần đối chiếu trực quan với báo cáo gốc."
   changed=True; quarter_count+=1; field_count+=len(new_fields)

 by_period={str(i.get("period")):i for i in items if isinstance(i,dict)}
 for item in items:
  key=period_key(item) if isinstance(item,dict) else None
  if not key: continue
  year,quarter=key
  basis=item.get("cashflow_period_basis")
  if basis=="year_to_date":
   for quarterly_field,ytd_field in CASHFLOW_QUARTER_FROM_YTD.items():
    if quarterly_field in set(item.get("financial_line_items_rejected_fields") or []): continue
    current=item.get(ytd_field)
    if not isinstance(current,(int,float)): continue
    if quarter==1:
     calc=current; formula="Q1 equals YTD Q1"
    else:
     previous=by_period.get(f"{year}-Q{quarter-1}") or {}
     prev=previous.get(ytd_field)
     if previous.get("cashflow_period_basis")!="year_to_date" or not isinstance(prev,(int,float)): continue
     calc=current-prev; formula="current YTD minus previous quarter YTD"
    value=int(round(calc))
    if item.get(quarterly_field)!=value:
     item[quarterly_field]=value
     item[quarterly_field+"_calculation"]=formula
     changed=True; field_count+=1
  elif basis=="quarterly_reported":
   for quarterly_field,ytd_field in CASHFLOW_QUARTER_FROM_YTD.items():
    current=item.get(ytd_field)
    if isinstance(current,(int,float)) and item.get(quarterly_field) is None:
     item[quarterly_field]=int(round(current))
     item[quarterly_field+"_calculation"]="reported as standalone quarter"
     changed=True; field_count+=1
  if quarter>1 and basis=="year_to_date":
   previous=by_period.get(f"{year}-Q{quarter-1}") or {}
   prev_cash=previous.get("cash_ending")
   if isinstance(prev_cash,(int,float)) and item.get("cash_beginning")!=prev_cash:
    item["cash_beginning"]=prev_cash
    item["cash_beginning_calculation"]="previous quarter closing cash"
    changed=True; field_count+=1
 # Hide auto-extracted cash beginning/ending balances when their bridge to
 # the separately reported quarterly cash change does not reconcile.
 for item in items:
  if not isinstance(item,dict) or not item.get("financial_line_items_status"): continue
  fields=set(item.get("financial_line_items_extracted_fields") or [])
  cash_begin=item.get("cash_beginning")
  cash_end=item.get("cash_ending")
  cash_change=item.get("net_cash_change")
  asset_total=item.get("total_assets")
  if all(isinstance(v,(int,float)) for v in (cash_begin,cash_end,cash_change)):
   tolerance=max(abs(asset_total)*0.02,1000) if isinstance(asset_total,(int,float)) else 1000
   if abs((cash_end-cash_begin)-cash_change)>tolerance:
    removed=[]
    for field in ("cash_beginning","cash_ending"):
     if field in fields:
      item.pop(field,None); fields.discard(field); removed.append(field); changed=True
    if removed:
     item["financial_line_items_extracted_fields"]=sorted(fields)
     item["financial_line_items_cash_check"]="opening/closing cash hidden because the cash bridge did not reconcile"
     item["financial_line_items_note"]=str(item.get("financial_line_items_note") or "")+" Số dư tiền đầu/cuối kỳ bị ẩn do không khớp biến động tiền theo quý."
     field_count+=len(removed)
 reconciled,reconciled_quarters,reconciled_fields=reconcile_detail_items(items,symbol)
 changed=changed or reconciled
 quarter_count+=reconciled_quarters
 field_count+=reconciled_fields
 if changed:
  path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return changed,quarter_count,field_count

def main():
 files=sorted(DATA.glob("financials-*.json"))
 changed_files=changed_quarters=changed_fields=0
 for path in files:
  try:
   changed,quarters,fields=enrich_snapshot(path)
   if changed:
    changed_files+=1; changed_quarters+=quarters; changed_fields+=fields
    print(f"{path.name}: {quarters} quarter(s) enriched, {fields} field updates")
  except Exception as exc:
   print(f"::warning::{path.name}: {exc}")
 print(f"Financial category enrichment: {len(files)} snapshots; {changed_files} changed; {changed_quarters} quarter(s) enriched; {changed_fields} field updates.")
 return 0

if __name__=="__main__":
 raise SystemExit(main())
