#!/usr/bin/env python3
"""Enrich quarterly BCTC snapshots from PDF/ZIP text already archived from VietstockFinance.

Only fills missing fields. Text/OCR-derived fields are marked pending visual review.
No prices, market multiples or other values are inferred from accounting reports.
"""
from __future__ import annotations
import hashlib, json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = ROOT / "reports" / "raw"
REPORT_QUEUE = ROOT / "config" / "report-queue.json"
_QUEUE_ARCHIVE_BY_URL = None
DETAIL_SCHEMA_VERSION = "2026-10-22-bank-statement-qc-v4"
CORE_EXTRACTION_DEBUG_VERSION = "2026-10-23-bid-balance-source-v2"
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])\(?-?\d[\d.,]*\d?\)?")
BANKS = {"MBB", "ACB", "SHB", "TCB", "TPB", "VPB", "STB", "VCB", "CTG", "BID"}
BROKERS = {"HCM", "SHS", "TCX", "VND", "VCI", "VCK", "VIX", "SSI", "VDS"}
STANDARD_BUSINESSES = {"BSR", "FPT", "NLG", "VHM", "KDH", "NVL", "HHV", "DPG", "GAS", "PLX", "IDC", "KBC", "GEG"}

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
BANK_BALANCE_LABELS = {
 "bank_cash_on_hand":["tien mat, vang bac, da quy","tien mat vang bac da quy"],
 "bank_deposits_at_state_bank":["tien gui tai nhnn","tien gui tai ngan hang nha nuoc"],
 "bank_deposits_and_loans_to_credit_institutions":["tien gui va cho vay cac tctd khac","tien gui va cho vay cac to chuc tin dung khac"],
 "bank_customer_loans":["cho vay khach hang","cho vay khichhing","chovaykhachhang","cho vay khach hang tong"],
 "bank_trading_securities":["chung khoan kinh doanh"],
 "bank_derivatives_and_other_financial_assets":["cac cong cu tai chinh phai sinh va cac tai san tai chinh khac"],
 "bank_investment_securities":["chung khoan dau tu"],
 "bank_contributions_and_long_term_investments":["gop von, dau tu dai han","gop von dau tu dai han"],
 "bank_other_assets":["tai san co khac"],
 "bank_deposits_and_borrowings_from_credit_institutions":["tien gui va tien vay cac tctd khac","tien gui va vay cac tctd khac","tien gui va vay cac to chuc tin dung khac"],
 "bank_customer_deposits":["tien gui cua khach hang"],
 "bank_valuable_papers":["phat hanh giay to co gia"],
 "bank_funding_and_trust_liabilities":["von tai tro, uy thac dau tu"],
 "bank_other_liabilities":["cac khoan no khac","cac khoan ngkhc","no khac"],
}
BROKER_BALANCE_LABELS = {
 "broker_fvtpl_assets":["tai san tai chinh ghi nhan thong qua lai lo","tai san tai chinh ghi nhan thong qua lai/lo"],
 "broker_held_to_maturity_assets":["cac khoan dau tu nam giu den ngay dao han","dau tu nam giu den ngay dao han"],
 "broker_lending_assets":["cac khoan cho vay"],
 "broker_afs_assets":["tai san tai chinh san sang de ban"],
 "broker_receivables":["cac khoan phai thu"],
 "broker_short_term_borrowings":["vay va no thue tai chinh ngan han","vay ngan han"],
 "broker_short_term_bonds":["trai phieu phat hanh ngan han"],
 "broker_long_term_bonds":["trai phieu phat hanh dai han"],
 "broker_customer_deposits":["tien gui cua khach hang"],
}
BROKER_INCOME_LABELS = {
 "broker_fvtpl_gain":["lai/(lo) tu cac tai san tai chinh ghi nhan thong qua lai lo","lai tu cac tai san tai chinh ghi nhan thong qua lai lo","lai tu tai san tai chinh ghi nhan thong qua lai lo"],
 "broker_held_to_maturity_income":["lai tu cac khoan dau tu nam giu den ngay dao han"],
 "broker_lending_income":["lai tu cac khoan cho vay va phai thu","thu nhap tu cac khoan cho vay"],
 "broker_afs_income":["lai tu tai san tai chinh san sang de ban"],
 "broker_brokerage_revenue":["doanh thu nghiep vu moi gioi chung khoan","doanh thu moi gioi chung khoan"],
 "broker_underwriting_revenue":["doanh thu nghiep vu bao lanh, dai ly phat hanh chung khoan","doanh thu bao lanh, dai ly phat hanh chung khoan"],
 "broker_advisory_revenue":["doanh thu nghiep vu tu van dau tu chung khoan","doanh thu tu van dau tu chung khoan"],
 "broker_custody_revenue":["doanh thu nghiep vu luu ky chung khoan","doanh thu luu ky chung khoan"],
 "broker_financial_advisory_revenue":["doanh thu hoat dong tu van tai chinh"],
 "broker_other_operating_income":["thu nhap tu hoat dong khac"],
 "broker_operating_expenses":["chi phi hoat dong","cong chi phi hoat dong"],
 "broker_admin_expenses":["chi phi quan ly cong ty chung khoan","chi phi quan ly doanh nghiep"],
 "broker_net_operating_profit":["loi nhuan thuan tu hoat dong kinh doanh"],
 "broker_total_operating_revenue":["cong doanh thu hoat dong","tong doanh thu hoat dong","tong cong doanh thu hoat dong"],
 "broker_total_operating_expenses":["cong chi phi hoat dong","tong chi phi hoat dong"],
 "broker_fvtpl_loss":["lo cac tai san tai chinh ghi nhan thong qua lai lo","lo cac tai san tai chinh ghi nhan thong qua lai/lo","lo tu cac tai san tai chinh ghi nhan thong qua lai lo","lo tu cac tai san tai chinh ghi nhan thong qua lai/lo"],
 "broker_lending_cost":["chi phi di vay cua cac khoan cho vay","chi phi di vay cho cac khoan cho vay"],
 "broker_trading_expense":["chi phi hoat dong tu doanh"],
 "broker_advisory_expense":["chi phi nghiep vu tu van tai chinh","chi phi tu van tai chinh"],
 "broker_brokerage_expense":["chi phi nghiep vu moi gioi chung khoan","chi phi moi gioi chung khoan"],
 "broker_custody_expense":["chi phi nghiep vu luu ky chung khoan","chi phi luu ky chung khoan"],
 "broker_other_operating_expense":["chi phi hoat dong khac"],
 "broker_financial_income":["doanh thu hoat dong tai chinh"],
 "broker_financial_expense":["chi phi tai chinh"],
 "broker_interest_expense":["chi phi lai vay"],
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
 "net_profit_attributable":["loi nhuan sau thue cua co dong cong ty me","loi nhuan sau thue cua co dong cua cong ty me","loi nhuan thuoc ve co dong cong ty me","loi nhuan thuan co dong ngan hang"],
}
BANK_INCOME_LABELS = {
 "bank_interest_income":["thu nhap lai va cac khoan thu nhap tuong tu"],
 "bank_interest_expense":["chi phi lai va cac khoan chi phi tuong tu"],
 "bank_net_interest_income":["thu nhap thuan tu lai","thu nhap lai thuan"],
 "bank_service_income":["thu nhap tu hoat dong dich vu"],
 "bank_service_expense":["chi phi hoat dong dich vu"],
 "bank_net_service_income":["lai/lo thuan tu hoat dong dich vu","lai lo thuan tu hoat dong dich vu","lai thuan tu hoat dong dich vu"],
 "bank_fx_net_income":["lai thuan tu hoat dong kinh doanh ngoai hoi"],
 "bank_trading_securities_net":["lai thuan tu mua ban chung khoan kinh doanh"],
 "bank_investment_securities_net":["lai thuan tu mua ban chung khoan dau tu","lai thuan tu mua ban chung khoan dau tu va gop von dau tu dai han"],
 "bank_other_operating_net":["lai thuan tu hoat dong kinh doanh khac"],
 "bank_dividend_and_capital_income":["thu nhap tu gop von, mua co phan"],
 "bank_operating_expenses":["tong chi phi hoat dong","chi phi hoat dong"],
 "bank_pre_provision_operating_profit":["loi nhuan thuan tu hoat dong kinh doanh truoc chi phi du phong rui ro"],
 "bank_provision_expense":["chi phi du phong rui ro"],
 "bank_non_controlling_profit":["loi ich cua co dong khong kiem soat"],
}
CASHFLOW_LABELS = {
 "operating_cash_flow_ytd":["luu chuyen tien thuan tu hoat dong kinh doanh","luu chuyen tien tu hoat dong kinh doanh"],
 "investing_cash_flow_ytd":["luu chuyen tien thuan tu hoat dong dau tu","luu chuyen tien tu hoat dong dau tu"],
 "financing_cash_flow_ytd":["luu chuyen tien thuan tu hoat dong tai chinh","luu chuyen tien thuan tu hoat dong taichinh","luu chuyen tien thuan tu hoat dong taichinn","luu chuyen tien tu hoat dong tai chinh"],
 "capital_expenditure_ytd":["tien chi de mua sam xay dung tai san co dinh","tien chi mua sam xay dung tai san co dinh","mua sam xay dung tai san co dinh va cac tai san dai han khac"],
 "dividends_paid_ytd":["co tuc loi nhuan da tra cho chu so huu","tien chi tra co tuc loi nhuan cho chu so huu"],
 "net_cash_change_ytd":["luu chuyen tien thuan trong ky","luu chuyen tien thuan trong nam"],
 "cash_beginning":[
  "tien va cac khoan tuong duong tien tai thoi diem dau ky",
  "tien va cac khoan tuong duong tien tai thoi diem dau",
  "tien va cac khoan tuong duong tien dau ky",
  "tien va tuong duong tien dau ky",
 ],
 "cash_ending":[
  "tien va cac khoan tuong duong tien tai thoi diem cuoi ky",
  "tien va cac khoan tuong duong tien tai thoi diem cuoi",
  "tien va cac khoan tuong duong tien cuoi ky",
  "tien va tuong duong tien cuoi ky",
 ],
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
 "cash_beginning":"60","foreign_exchange_effect_ytd":"61","cash_ending":"70",
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

STATEMENT_TERMS = {
 "balance":["bao cao tinh hinh tai chinh","bang can doi ke toan","statement of financial position"],
 "income":["bao cao ket qua hoat dong","bao cao ket qua hoat dong kinh doanh","bao cao ket qua kinh doanh","bao cao thu nhap","statement of profit or loss","statement of income","income statement"],
 "cashflow":["bao cao luu chuyen tien te","statement of cash flows","cash flow statement"],
}

def statement_heading_kind(page):
 text=norm(page.get("text",""))
 if "muc luc" in text or "table of contents" in text or "thuyet minh bao cao tai chinh" in text or "notes to the financial statements" in text:
  return None
 # Vietnamese bank statements use regulator form codes (B02/TCTD, B03/TCTD,
 # B04/TCTD), which OCR can preserve even when the title line is distorted.
 if re.search(r"\bb0?2\s*/\s*tctd\b",text):
  return "balance"
 if re.search(r"\bb0?3\s*/\s*tctd\b",text):
  return "income"
 if re.search(r"\bb0?4\s*/\s*tctd\b",text):
  return "cashflow"
 lines=[norm(line) for line in str(page.get("text","")).splitlines()[:45]]
 for line in lines:
  if not line or len(line)>155:
   continue
  for kind,terms in STATEMENT_TERMS.items():
   if any(term in line for term in terms):
    return kind
 return None

def select_statement_pages(pages,kind):
 ordered=sorted(
  [page for page in pages if isinstance(page,dict) and page.get("text")],
  key=lambda page:int(page.get("page") or 0)
 )
 kinds=[statement_heading_kind(page) for page in ordered]
 selected=[]
 for start,found_kind in enumerate(kinds):
  if found_kind!=kind:
   continue
  end=len(ordered)
  for idx in range(start+1,len(ordered)):
   if kinds[idx] and kinds[idx]!=kind:
    end=idx
    break
  selected.extend(ordered[start:end])
 unique={}
 for page in selected:
  unique[int(page.get("page") or 0)]=page
 return [unique[number] for number in sorted(unique)]

def unit_factor(pages,item):
 header=norm(" ".join(str(p.get("text",""))[:5000] for p in pages[:3]))
 # OCR frequently renders "Triệu VND" as "Tri~u VND", "Trifu VND",
 # or similar. Recognize these variants before falling back to the VND unit.
 if any(t in header for t in ("nghin dong","nghin vnd","thousand vnd")) or re.search(r"\bngh[a-z~._-]{0,4}n\s+(?:dong|vnd)\b",header): return 0.001
 if any(t in header for t in ("trieu dong","trieu vnd","million vnd")) or re.search(r"\btri[a-z~._-]{0,3}u\s+(?:dong|vnd)\b",header): return 1.0
 if any(t in header for t in ("ty dong","ty vnd","billion vnd")) or re.search(r"\bty\s+(?:dong|vnd)\b",header): return 1000.0
 if re.search(r"\bvnd\b",header) or "don vi tinh dong" in header: return 0.000001
 unit=norm(item.get("unit",""))
 if "trieu" in unit or "million" in unit: return 1.0
 if "nghin" in unit or "thousand" in unit: return 0.001
 if re.search(r"\bty\b",unit) or "billion" in unit: return 1000.0
 return 1.0

def is_statement_row_start(line):
 # OCR sometimes places a financial-statement code on its own line (e.g. "06")
 # before a wrapped label. Stop label matching at these row boundaries to avoid
 # borrowing figures from the next line item.
 raw=str(line or "")
 if re.fullmatch(r"\s*\d{1,3}(?:\.\d{1,2})?\s*",raw):
  return True
 if re.match(r"^\s*[A-Za-z]{1,3}\s*\|",raw):
  return True
 return bool(re.match(r"^\s*(?:\|\s*)?\d{1,3}(?:\.\d{1,2})?\s*(?:\||\s+\d{1,3}\s)",raw))

def value_by_label(pages,labels,factor,threshold=1000,exclude_terms=None):
 excludes=[norm(term) for term in (exclude_terms or [])]
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
     if any(term and term in combined for term in excludes):
      continue
     # Search after the complete label, including wrapped continuation lines.
     tail=combined[position+len(target):]
     vals=amounts(tail,threshold=threshold)
     if vals: return int(round(vals[0]*factor))
 return None

def value_by_code(pages,code,factor,threshold=1000):
 token=re.compile(r"(?<!\d)"+re.escape(code)+r"(?!\d)")
 for page in pages:
  for line in str(page.get("text","")).splitlines():
   matches=list(token.finditer(line))
   for match in reversed(matches):
    vals=[n for n in amounts(line[match.end():],threshold=threshold) if abs(n)>=threshold and not (1900 <= abs(n) <= 2100)]
    if vals: return int(round(vals[0]*factor))
 return None

def normalized_archive_url(url):
 parsed=urlparse(unquote(str(url or "").strip()))
 host=(parsed.hostname or "").casefold()
 path=unquote(parsed.path or "").rstrip("/").casefold()
 if not host or not path: return None
 return host,path

def queue_archive_index():
 global _QUEUE_ARCHIVE_BY_URL
 if _QUEUE_ARCHIVE_BY_URL is not None: return _QUEUE_ARCHIVE_BY_URL
 index={}
 try:
  payload=json.loads(REPORT_QUEUE.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError):
  _QUEUE_ARCHIVE_BY_URL={}
  return _QUEUE_ARCHIVE_BY_URL
 for job in payload.get("jobs",[]) if isinstance(payload,dict) else []:
  if not isinstance(job,dict): continue
  symbol=str(job.get("symbol") or "").strip().upper()
  if not symbol: continue
  for archived in job.get("downloadedFiles",[]) or []:
   if not isinstance(archived,dict) or archived.get("status")!="downloaded_needs_review": continue
   relative=str(archived.get("file") or "").replace("\\","/").strip()
   if not relative: continue
   archive=(ROOT/relative).resolve()
   try: archive.relative_to(RAW.resolve())
   except ValueError: continue
   if not archive.is_file() or not Path(str(archive)+".extracted.json").is_file(): continue
   record={
    "symbol":symbol,
    "period":str(archived.get("period") or ""),
    "path":archive.relative_to(ROOT).as_posix(),
   }
   for url_key in ("url","final_url","source_url"):
    key=normalized_archive_url(archived.get(url_key))
    if key: index.setdefault(key,[]).append(record)
 _QUEUE_ARCHIVE_BY_URL=index
 return index

def resolve_archive_source(item,symbol):
 existing=str(item.get("source_archive_file") or "").strip()
 if existing:
  archive=(ROOT/existing).resolve()
  try: archive.relative_to(RAW.resolve())
  except ValueError: existing=""
  else:
   if archive.is_file() and Path(str(archive)+".extracted.json").is_file(): return archive.relative_to(ROOT).as_posix()
 key=normalized_archive_url(item.get("source_url"))
 if not key: return ""
 candidates=queue_archive_index().get(key,[])
 same_symbol=[x for x in candidates if x.get("symbol")==str(symbol).upper()]
 if not same_symbol: return ""
 period=str(item.get("period") or "")
 same_period=[x for x in same_symbol if x.get("period")==period]
 chosen=(same_period or same_symbol)[0]
 return str(chosen.get("path") or "")

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

def value_by_row_prefix(pages,prefix_patterns,factor,threshold=1000):
 patterns=[re.compile(pattern) for pattern in prefix_patterns]
 for page in pages:
  lines=str(page.get("text","")).splitlines()
  for index,line in enumerate(lines):
   clean=norm(line)
   if not any(pattern.search(clean) for pattern in patterns):
    continue
   vals=amounts(line,threshold=threshold)
   if not vals:
    for lookahead in range(index+1,min(index+3,len(lines))):
     if is_statement_row_start(lines[lookahead]): break
     vals=amounts(lines[lookahead],threshold=threshold)
     if vals: break
   if vals:
    return int(round(vals[0]*factor))
 return None

def is_quarter_comparison_page(page):
 text=norm(page.get("text",""))
 has_unit=(
  "trieu dong" in text or "trieu vnd" in text or "million vnd" in text
  or "don vi tinh trieu" in text
 )
 has_profit_rows=(
  ("loi nhuan truoc thue" in text or "profit before tax" in text)
  and ("loi nhuan sau thue" in text or "profit after tax" in text)
 )
 # A quarterly filing may title the page "Quý II ... and six months ended"
 # rather than explicitly saying "same period". That wording still means
 # the table can have quarterly columns followed by YTD columns.
 has_comparison=any(term in text for term in (
  "tang","giam","increase","decrease","same period","cung ky",
  "nam truoc","nam nay","ky truoc","prior year","previous year",
  "prior period","previous period"
 ))
 has_quarter=any(term in text for term in ("quy ","quarter ended","quarter of","quy i","quy ii","quy iii","quy iv"))
 pbt_values=0
 net_values=0
 for line in str(page.get("text","")).splitlines():
  clean=norm(line)
  if ("loi nhuan truoc thue" in clean or "profit before tax" in clean) and not pbt_values:
   pbt_values=len(amounts(line))
  if ("loi nhuan sau thue" in clean or "profit after tax" in clean) and not net_values:
   net_values=len(amounts(line))
 # At least three values on each profit row indicate a standalone-quarter
 # column plus comparison/YTD columns. Two-column YTD-only pages are not
 # treated as a standalone-quarter statement.
 has_quarter_columns=pbt_values>=3 and net_values>=3
 return has_unit and has_profit_rows and has_comparison and has_quarter and has_quarter_columns

def value_by_table_label(pages,labels,factor,threshold=1000):
 # Use values from the table after its unit declaration, not narrative values
 # stated in billions on the disclosure cover page.
 for page in pages:
  lines=str(page.get("text","")).splitlines()
  normalized=[norm(line) for line in lines]
  unit_indexes=[
   idx for idx,line in enumerate(normalized)
   if ("trieu dong" in line or "trieu vnd" in line or "million vnd" in line)
   and (("don vi" in line) or ("unit" in line) or "%" in line)
  ]
  if not unit_indexes:
   continue
  for label in labels:
   target=norm(label)
   for start in range(unit_indexes[0]+1,len(lines)):
    parts=[]
    for end in range(start,min(start+4,len(lines))):
     if end>start and is_statement_row_start(lines[end]): break
     parts.append(lines[end])
     combined=norm(" ".join(parts))
     position=combined.find(target)
     if position<0: continue
     tail=combined[position+len(target):]
     vals=amounts(tail,threshold=threshold)
     if len(vals)>=2:
      return int(round(vals[0]*factor))
 return None

def extract_core_fields(item,symbol,pages,detail_found,mode):
 out={}
 calculations={}
 balance=select_statement_pages(pages,"balance")
 income=select_statement_pages(pages,"income")
 summary_pages=[page for page in pages if is_quarter_comparison_page(page)]
 # A small number of Vietstock ZIP archives start with a disclosure covering
 # both separate and consolidated reports. Never take a stand-alone summary
 # table from that mixed document to populate a consolidated snapshot.
 archive_path=str(item.get("source_archive_file") or "").lower()
 first_text=norm(" ".join(str(page.get("text",""))[:3500] for page in pages[:3]))
 mixed_separate_disclosure=(
  archive_path.endswith(".zip")
  and any(term in first_text for term in (
   "bao cao tai chinh rieng le", "bao cao rieng le",
   "separate financial statement", "separate financial statements"
  ))
 )
 if mixed_separate_disclosure:
  summary_pages=[
   page for page in summary_pages
   if any(term in norm(page.get("text","")) for term in (
    "loi nhuan sau thue hop nhat",
    "consolidated profit after tax",
    "consolidated result of operations",
    "bao cao ket qua hoat dong hop nhat"
   ))
  ]
 unit_pages=balance or summary_pages or income or select_statement_pages(pages,"cashflow") or pages
 factor=unit_factor(unit_pages,item)

 assets=value_by_label(
  balance,["tong cong tai san","tong tai san","total assets"],factor,
  exclude_terms=["tai san ngan han","tai san dai han"]
 ) if balance else None
 if assets is None and balance:
  # Do not fall back to the "A. Tài sản" section heading: it is not a total
  # and would silently capture the first component (e.g. cash). OCR sometimes
  # joins "tài sản" into "taisan", so allow optional whitespace in total labels.
  assets=value_by_row_prefix(
   balance,[
    r"^\s*(?:\|\s*)?(?:tong\s*)?(?:cong\s*)?tai\s*san\s*co(?:\s|$)",
    r"^\s*(?:\|\s*)?(?:tong\s*)?(?:cong\s*)?tai\s*san(?:\s|$)",
    r"^\s*(?:\|\s*)?total\s*assets(?:\s|$)"
   ],factor
  )

 equity_labels=["tong cong von chu so huu","tong von chu so huu","von chu so huu","total equity"]
 if symbol in BANKS:
  # Some bank B02/TCTD templates label equity as "Vốn và các quỹ"; prioritize
  # it before the generic "vốn chủ sở hữu" substring in the total-sources row.
  equity_labels=["von va cac quy"]+equity_labels
 equity=value_by_label(
  balance,equity_labels,factor,
  exclude_terms=["no phai tra","liabilities and equity"]
 ) if balance else None
 source_total=value_by_label(
  balance,[
   "tong cong nguon von","tong nguon von",
   "tong no phai tra va von chu so huu","no phai tra va von chu so huu",
   "total liabilities and equity","total sources"
  ],factor
 ) if balance else None
 if source_total is None and balance:
  source_total=value_by_row_prefix(
   balance,[r"^\s*(?:\|\s*)?b\.?\s+no phai tra.*von chu so huu(?:\s|$)",
            r"^\s*total liabilities and equity(?:\s|$)"],factor
  )
 # Some bank PDFs/OCR put the source totals BEFORE the wrapped final word
 # in "Tổng nợ phải trả và vốn chủ sở hữu". Recover that total only when
 # the adjacent lines complete the label and a candidate total reconciles
 # to the independently extracted total-assets row.
 if balance and symbol in BANKS:
  # Run this even when a generic text matcher already returned a number:
  # it may have picked the first liability component from the section heading.
  # Accept the wrapped total row without requiring the OCR to preserve the final
  # word "hữu"; the independent assets match is the verification gate.
  for page in balance:
   lines=str(page.get("text","")).splitlines()
   for index,line in enumerate(lines):
    clean_window=norm(" ".join(lines[index:index+3]))
    if not re.search(r"tong\s*no\s*phai\s*tra", clean_window) or not re.search(r"von\s*chu\s*so", clean_window):
     continue
    row_values=amounts(line,threshold=1000)
    if not row_values:
     for lookahead in range(index+1,min(index+4,len(lines))):
      if is_statement_row_start(lines[lookahead]):
       break
      row_values=amounts(lines[lookahead],threshold=1000)
      if row_values:
       break
    if not row_values or not isinstance(assets,(int,float)):
     continue
    candidates=[int(round(value*factor)) for value in row_values]
    candidate=min(candidates,key=lambda value:abs(value-assets))
    tolerance=max(abs(assets)*0.00001,1000)
    if abs(candidate-assets)<=tolerance:
     source_total=candidate
     break
   if source_total is not None and isinstance(assets,(int,float)) and abs(source_total-assets)<=max(abs(assets)*0.00001,1000):
    break
 liabilities=value_by_label(
  balance,["tong cong no phai tra","tong no phai tra","total liabilities"],factor,
  exclude_terms=["von chu so huu","liabilities and equity"]
 ) if balance else None

 tolerance=max(5.0,abs(assets)*0.00001) if isinstance(assets,(int,float)) else 5.0
 source_matches_assets=(
  isinstance(assets,(int,float)) and isinstance(source_total,(int,float))
  and abs(assets-source_total)<=tolerance
 )
 # If the independently matched total-sources row equals total assets,
 # a weak liability-label match may have captured the whole total or one
 # component of liabilities. Keep a parsed subtotal only if the accounting
 # equation already reconciles; otherwise derive liabilities from reported
 # equity and retain a hard equation check below.
 if source_matches_assets and isinstance(equity,(int,float)) and equity>0:
  candidate=assets-equity
  if candidate>=0 and (
   not isinstance(liabilities,(int,float))
   or abs(assets-liabilities-equity)>3
  ):
   liabilities=int(round(candidate))
   calculations["total_liabilities"]="total_assets minus reported equity; total sources matched total assets"
 if source_matches_assets and isinstance(liabilities,(int,float)) and equity is None:
  candidate=assets-liabilities
  if candidate>=0:
   equity=int(round(candidate))
   calculations["equity"]="total_assets minus reported liabilities; total sources matched total assets"

 if symbol=="BID":
  def debug_money(value):
   return None if value is None else int(round(value))
  print(
   "[CORE_DEBUG]",
   CORE_EXTRACTION_DEBUG_VERSION,
   item.get("period"),
   {
    "balance_pages":[int(page.get("page") or 0) for page in balance],
    "factor":factor,
    "assets":debug_money(assets),
    "liabilities":debug_money(liabilities),
    "equity":debug_money(equity),
    "source_total":debug_money(source_total),
    "source_matches_assets":bool(source_matches_assets),
    "equation_delta":(
     debug_money(assets-liabilities-equity)
     if all(isinstance(v,(int,float)) for v in (assets,liabilities,equity)) else None
    ),
   },
  )
  shown=0
  for page in balance:
   for line in str(page.get("text","")).splitlines():
    clean=norm(line)
    if any(term in clean for term in (
     "tong tai san co","tong cong tai san","von va cac quy",
     "tong no phai tra va von chu so huu","tong no phai tra va von chu so huu"
    )):
     print("[CORE_DEBUG_ROW]", item.get("period"), int(page.get("page") or 0), line[:260])
     shown+=1
     if shown>=6: break
   if shown>=6: break
 balance_valid=(
  isinstance(assets,(int,float)) and isinstance(liabilities,(int,float)) and isinstance(equity,(int,float))
  and assets>0 and liabilities>=0 and equity>=0
  and abs(assets-liabilities-equity)<=3
 )
 if balance_valid:
  out["total_assets"]=int(round(assets))
  out["total_liabilities"]=int(round(liabilities))
  out["equity"]=int(round(equity))
 elif any(isinstance(value,(int,float)) for value in (assets,liabilities,equity)):
  calculations["balance_totals_withheld"]="asset/liability/equity totals did not fully reconcile"

 profit_pages=summary_pages
 year,quarter=period_key(item) or (0,0)
 if not profit_pages and (quarter==1 or not mode):
  profit_pages=income
 pbt_labels=[
  "tong loi nhuan truoc thue","tong loi nhuan ke toan truoc thue",
  "loi nhuan ke toan truoc thue","loi nhuan truoc thue","profit before tax"
 ]
 net_labels=[
  "loi nhuan sau thue thu nhap doanh nghiep","loi nhuan sau thue","profit after tax"
 ]
 if summary_pages:
  # The selected page is already identified as a quarterly comparative table.
  # Parse from the text after the exact row label; this handles OCR variants
  # where the unit/header is split across lines and value_by_table_label misses it.
  pbt=value_by_label(summary_pages,pbt_labels,factor)
  net=value_by_label(summary_pages,net_labels,factor)
  if pbt is None:
   pbt=value_by_table_label(summary_pages,pbt_labels,factor)
  if net is None:
   net=value_by_table_label(summary_pages,net_labels,factor)
 else:
  pbt=value_by_label(profit_pages,pbt_labels,factor) if profit_pages else None
  net=value_by_label(profit_pages,net_labels,factor) if profit_pages else None
 if pbt is not None:
  out["pretax_profit"]=pbt
 if net is not None:
  out["net_profit"]=net
 parent_profit=value_by_label(
  profit_pages,
  ["loi nhuan thuan co dong ngan hang","loi nhuan sau thue cua co dong cong ty me",
   "loi nhuan sau thue cua co dong cua cong ty me","loi nhuan thuoc ve co dong cong ty me"],
  factor
 ) if profit_pages else None
 if parent_profit is not None:
  out["net_profit_attributable"]=parent_profit
 eps=value_by_label(
  profit_pages,["lai co ban tren co phieu","lai co ban tren co phieu vnd",
   "earnings per share"],1.0,threshold=50
 ) if profit_pages else None
 if eps is not None and abs(eps)<1000000:
  out["eps"]=eps
 if isinstance(detail_found.get("revenue"),(int,float)):
  out["revenue"]=detail_found["revenue"]
 elif symbol in BANKS and profit_pages:
  bank_revenue=value_by_label(
   profit_pages,["tong thu nhap hoat dong","tong thu nhap hoat dong kinh doanh"],factor
  )
  if bank_revenue is not None:
   out["revenue"]=bank_revenue
 out["__core_calculations"]=calculations
 out["__core_pages"]=sorted({
  int(page.get("page")) for page in balance+income+summary_pages
  if str(page.get("page","")).isdigit()
 })
 return out


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
 if symbol in BANKS and bal:
  for field,labels in BANK_BALANCE_LABELS.items():
   val=value_by_label(bal,labels,scale)
   if val is not None: out[field]=val
 if symbol in BROKERS and bal:
  for field,labels in BROKER_BALANCE_LABELS.items():
   val=value_by_label(bal,labels,scale)
   if val is not None: out[field]=val
 if symbol in BANKS:
  # Do not label net interest income as total operating income. If the statement
  # has no explicit aggregate, the aggregate is calculated from reconciled
  # quarterly components in apply_quarter_scope().
  revlabels=["tong thu nhap hoat dong","tong thu nhap hoat dong kinh doanh"]
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
 if symbol in BANKS and inc:
  for field,labels in BANK_INCOME_LABELS.items():
   if field=="bank_operating_expenses":
    val=value_by_label(inc,["chi phi hoat dong"],scale,exclude_terms=["chi phi hoat dong dich vu","chi phi hoat dong khac","chi phi hoat dong tai chinh"])
   elif field in {"bank_net_interest_income","bank_net_service_income"}:
    val=None
   else:
    val=value_by_label(inc,labels,scale)
   if val is not None: out[field]=val
 if symbol in BROKERS and inc:
  for field,labels in BROKER_INCOME_LABELS.items():
   val=value_by_label(inc,labels,scale)
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
  # Exclude the subtotal "before changes in operating assets and working
  # capital"; the actual net operating cash-flow row appears later and is the
  # value that belongs in the quarterly cash-flow category.
  excludes=(
   ["truoc nhung thay doi ve tai san va von luu dong",
    "before changes in operating assets and liabilities"]
   if field=="operating_cash_flow_ytd" else None
  )
  val=value_by_label(cf,labels,scale,exclude_terms=excludes) if cf else None
  if val is None and symbol in STANDARD_BUSINESSES and cf: val=value_by_code(cf,CASHFLOW_CODES[field],scale)
  if val is not None: out[field]=val
 if symbol in STANDARD_BUSINESSES and inc:
  basic_eps=value_by_code(inc,"70",1.0,threshold=50)
  diluted_eps=value_by_code(inc,"71",1.0,threshold=50)
  if basic_eps is not None and abs(basic_eps)<1000000: out["eps"]=basic_eps
  if diluted_eps is not None and abs(diluted_eps)<1000000: out["diluted_eps"]=diluted_eps
 if cf:
  cft=norm(" ".join(str(p.get("text","")) for p in cf))
  is_ytd=bool(
   re.search(r"\b01\s*/\s*01\s*/?\s*20\d{2}\b",cft)
   or "tu ngay 01 thang 01" in cft
   or "luy ke tu dau nam" in cft
   or "giai doan tu 01/01" in cft
   or re.search(r"\b(?:cho )?ky (?:6|9|12) thang ket thuc ngay\b",cft)
   or re.search(r"\bfor the (?:six|nine|twelve) months ended\b",cft)
   or re.search(r"\b(?:cho )?nam ket thuc ngay\b",cft)
   or re.search(r"\bfor the year ended\b",cft)
  )
  out["__cashflow_period_basis"]="year_to_date" if is_ytd else "quarterly_reported"
 return out

def period_key(item):
 m=re.fullmatch(r"(20\d{2})-Q([1-4])",str(item.get("period","")))
 return (int(m.group(1)),int(m.group(2))) if m else None


INCOME_DETAIL_FIELDS = (
 set(INCOME_LABELS)
 | set(BANK_INCOME_LABELS)
 | set(BROKER_INCOME_LABELS)
 | {"revenue", "income_tax_current", "income_tax_deferred", "net_profit_attributable"}
) - {"income_tax"}


def cumulative_income_mode(item, pages):
 key=period_key(item)
 if not key:
  return ""
 text=norm(" ".join(str(p.get("text","")) for p in select_statement_pages(pages,"income")))
 if not text:
  return ""
 # If the comparative profit table contains 3+ figures per row, it already
 # has standalone-quarter columns (usually Qn this year, Qn last year,
 # year-to-date this year and year-to-date last year). Do not subtract Q1
 # from these quarterly values again.
 if any(is_quarter_comparison_page(page) for page in pages):
  return ""
 has_three_month_columns=bool(
  re.search(r"\b(?:cho )?ky 3 thang ket thuc ngay\b",text)
  or re.search(r"\bfor the three months ended\b",text)
  or re.search(r"\bthree months ended\b",text)
 )
 year,quarter=key
 if quarter==2 and not has_three_month_columns and (
  re.search(r"\b(?:cho )?ky 6 thang ket thuc ngay\b",text)
  or re.search(r"\bfor the six months ended\b",text)
  or re.search(r"\bsix months ended\b",text)
 ):
  return "cumulative_6m"
 if quarter==3 and not has_three_month_columns and (
  re.search(r"\b(?:cho )?ky 9 thang ket thuc ngay\b",text)
  or re.search(r"\bfor the nine months ended\b",text)
  or re.search(r"\bnine months ended\b",text)
 ):
  return "cumulative_9m"
 if quarter==4 and not has_three_month_columns and (
  re.search(r"\bnam ket thuc ngay\b",text)
  or re.search(r"\bfor the year ended\b",text)
  or re.search(r"\byear ended\b",text)
 ):
  return "cumulative_fy"
 return ""


def apply_quarter_scope(item, items, found, symbol, mode):
 """Convert cumulative income rows to standalone-quarter values when possible.

 If the prior-quarter detail is unavailable, suppress those rows instead of
 displaying a six-/nine-/twelve-month total as a quarterly figure.
 """
 if not mode:
  return found, []
 key=period_key(item)
 if not key:
  return found, []
 year,quarter=key
 prior_periods=[f"{year}-Q{q}" for q in range(1,quarter)]
 by_period={str(row.get("period")):row for row in items if isinstance(row,dict)}
 old_fields=set(item.get("financial_line_items_extracted_fields") or [])
 withheld=[]
 reason="cumulative income value withheld; standalone quarter could not be reconciled to all prior-quarter detail rows"
 for field in sorted(INCOME_DETAIL_FIELDS):
  if symbol in BANKS and field=="revenue":
   # Bank operating income is rebuilt after the component rows are quarterized.
   continue
  existing_is_machine_field=field in old_fields and isinstance(item.get(field),(int,float))
  candidate=found.get(field)
  if isinstance(candidate,(int,float)):
   prior_values=[(by_period.get(period) or {}).get(field) for period in prior_periods]
   if prior_values and all(isinstance(value,(int,float)) for value in prior_values):
    found[field]=int(round(candidate-sum(prior_values)))
   else:
    found.pop(field,None)
    withheld.append(field)
    if existing_is_machine_field:
     item.setdefault("financial_line_items_prior_values",{}).setdefault(field,item[field])
     item.setdefault("financial_line_items_value_corrections",{})[field]={
      "previous_value":item[field],
      "reason":reason,
     }
     item.pop(field,None)
     old_fields.discard(field)
  elif existing_is_machine_field:
   # Old cumulative/mis-scaled fields must not remain visible when the
   # current report no longer provides a safely quarterized replacement.
   item.setdefault("financial_line_items_prior_values",{}).setdefault(field,item[field])
   item.setdefault("financial_line_items_value_corrections",{})[field]={
    "previous_value":item[field],
    "reason":reason,
   }
   item.pop(field,None)
   old_fields.discard(field)
   withheld.append(field)

 if symbol in BANKS:
  components=[
   "bank_net_interest_income", "bank_net_service_income", "bank_fx_net_income",
   "bank_trading_securities_net", "bank_investment_securities_net",
   "bank_other_operating_net", "bank_dividend_and_capital_income",
  ]
  if isinstance(found.get("revenue"),(int,float)):
   # Only quarterize an explicitly reported aggregate if the prior quarter
   # has the matching aggregate; otherwise it is handled as a missing detail.
   candidate=found["revenue"]
   prior_values=[(by_period.get(period) or {}).get("revenue") for period in prior_periods]
   if prior_values and all(isinstance(value,(int,float)) for value in prior_values):
    found["revenue"]=int(round(candidate-sum(prior_values)))
   else:
    found.pop("revenue",None)
    withheld.append("revenue")
  elif all(isinstance(found.get(field),(int,float)) for field in components):
   found["revenue"]=int(round(sum(found[field] for field in components)))
  elif "revenue" in old_fields and isinstance(item.get("revenue"),(int,float)):
   item.setdefault("financial_line_items_prior_values",{}).setdefault("revenue",item["revenue"])
   item.setdefault("financial_line_items_value_corrections",{})["revenue"]={
    "previous_value":item["revenue"],
    "reason":"previous parser mislabeled net interest income as total bank operating income",
   }
   item.pop("revenue",None)
   old_fields.discard("revenue")
   withheld.append("revenue")

 if old_fields!=set(item.get("financial_line_items_extracted_fields") or []):
  item["financial_line_items_extracted_fields"]=sorted(old_fields)
 return found, sorted(set(withheld))


def scale_mismatch(old_value,new_value):
 if not isinstance(old_value,(int,float)) or not isinstance(new_value,(int,float)):
  return False
 if old_value==0 or new_value==0 or (old_value<0)!=(new_value<0):
  return False
 return max(abs(old_value),abs(new_value))/max(min(abs(old_value),abs(new_value)),1) >= 1000

def sane_fields(item, found, symbol):
 # Cross-check extracted values against reconciled financial-statement totals.
 assets=item.get("total_assets")
 liabilities=item.get("total_liabilities")
 equity=item.get("equity")
 has_assets=isinstance(assets,(int,float)) and assets>0
 has_liabilities=isinstance(liabilities,(int,float)) and liabilities>=0
 has_equity=isinstance(equity,(int,float)) and equity>=0
 asset_fields={"current_assets","cash_and_equivalents","short_term_investments","short_term_receivables","inventory","non_current_assets","fixed_assets",
  "bank_cash_on_hand","bank_deposits_at_state_bank","bank_deposits_and_loans_to_credit_institutions","bank_customer_loans",
  "bank_trading_securities","bank_derivatives_and_other_financial_assets","bank_investment_securities",
  "bank_contributions_and_long_term_investments","bank_other_assets",
  "broker_fvtpl_assets","broker_held_to_maturity_assets","broker_lending_assets","broker_afs_assets","broker_receivables"}
 liability_fields={"current_liabilities","long_term_liabilities","bank_deposits_and_borrowings_from_credit_institutions",
  "bank_customer_deposits","bank_valuable_papers","bank_funding_and_trust_liabilities","bank_other_liabilities",
  "broker_short_term_borrowings","broker_short_term_bonds","broker_long_term_bonds","broker_customer_deposits"}
 retained_fields={"retained_earnings","bank_undistributed_profit"}
 income_fields={"revenue","cost_of_goods_sold","gross_profit","financial_income","financial_expense","interest_expense","selling_expense","admin_expense","operating_profit","income_tax","income_tax_current","income_tax_deferred","net_profit_attributable",
  "bank_interest_income","bank_interest_expense","bank_net_interest_income","bank_service_income","bank_service_expense",
  "bank_net_service_income","bank_fx_net_income","bank_trading_securities_net","bank_investment_securities_net",
  "bank_other_operating_net","bank_dividend_and_capital_income","bank_operating_expenses","bank_pre_provision_operating_profit",
  "bank_provision_expense","bank_non_controlling_profit","broker_fvtpl_gain","broker_held_to_maturity_income",
  "broker_lending_income","broker_afs_income","broker_brokerage_revenue","broker_underwriting_revenue",
  "broker_advisory_revenue","broker_custody_revenue","broker_financial_advisory_revenue","broker_other_operating_income",
  "broker_operating_expenses","broker_admin_expenses","broker_net_operating_profit",
  "broker_total_operating_revenue","broker_total_operating_expenses","broker_fvtpl_loss",
  "broker_brokerage_expense","broker_custody_expense","broker_other_operating_expense",
  "broker_lending_cost","broker_trading_expense","broker_advisory_expense",
  "broker_financial_income","broker_financial_expense","broker_interest_expense"}
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

  # Reconcile bank subtotals. Expenses are stored as positive statement values;
  # net income and profit lines therefore subtract the absolute expense values.
  if symbol in BANKS:
   unquarterized=set(item.get("financial_line_items_unquarterized_fields") or [])
   def set_derived(field,value,formula,reason):
    nonlocal period_changed,changed_fields
    if not isinstance(value,(int,float)) or not __import__("math").isfinite(value):
     return
    rounded=int(round(value))
    previous=item.get(field)
    if previous!=rounded:
     if isinstance(previous,(int,float)):
      prior.setdefault(field,previous)
      item.setdefault("financial_line_items_value_corrections",{})[field]={
       "previous_value":previous,"new_value":rounded,"reason":reason,
      }
     item[field]=rounded
     period_changed=True; changed_fields+=1
    if item.get(field+"_calculation")!=formula:
     item[field+"_calculation"]=formula
     period_changed=True; changed_fields+=1
    fields.add(field)
    if field in rejected:
     rejected.discard(field)
     rejected_values.pop(field,None)
     period_changed=True; changed_fields+=1

   interest_income=item.get("bank_interest_income")
   interest_expense=item.get("bank_interest_expense")
   if (
    isinstance(interest_income,(int,float)) and isinstance(interest_expense,(int,float))
    and not ({"bank_interest_income","bank_interest_expense"} & unquarterized)
   ):
    set_derived(
     "bank_net_interest_income",interest_income-abs(interest_expense),
     "Thu nhập lãi - |chi phí lãi| theo BCTC ngân hàng.",
     "derived from reported interest income minus reported interest expense",
    )

   service_income=item.get("bank_service_income")
   service_expense=item.get("bank_service_expense")
   if (
    isinstance(service_income,(int,float)) and isinstance(service_expense,(int,float))
    and not ({"bank_service_income","bank_service_expense"} & unquarterized)
   ):
    set_derived(
     "bank_net_service_income",service_income-abs(service_expense),
     "Thu nhập dịch vụ - |chi phí dịch vụ| theo BCTC ngân hàng.",
     "derived from reported service income minus reported service expense",
    )

   bank_components=[
    "bank_net_interest_income", "bank_net_service_income", "bank_fx_net_income",
    "bank_trading_securities_net", "bank_investment_securities_net",
    "bank_other_operating_net", "bank_dividend_and_capital_income",
   ]
   component_values=[item.get(field) for field in bank_components]
   components_safe=(
    all(isinstance(value,(int,float)) for value in component_values)
    and not (set(bank_components) & unquarterized)
    and not (set(bank_components) & rejected)
   )
   existing_revenue=item.get("revenue")
   # Prefer the reported pre-provision subtotal and operating expense over
   # summing subcomponents that OCR may miss or misread.
   reported_ppop=item.get("bank_pre_provision_operating_profit")
   reported_op_expense=item.get("bank_operating_expenses")
   if (
    isinstance(reported_ppop,(int,float)) and isinstance(reported_op_expense,(int,float))
    and not ({"bank_pre_provision_operating_profit","bank_operating_expenses"} & unquarterized)
    and not ({"bank_pre_provision_operating_profit","bank_operating_expenses"} & rejected)
   ):
    operating_income=int(round(reported_ppop+abs(reported_op_expense)))
    set_derived(
     "revenue",operating_income,
     "Lợi nhuận trước dự phòng + chi phí hoạt động; đối chiếu theo tổng phụ BCTC ngân hàng.",
     "derived from reported pre-provision operating profit plus positive operating expenses",
    )
   elif components_safe:
    operating_income=int(round(sum(component_values)))
    set_derived(
     "revenue",operating_income,
     "Tổng bảy cấu phần thu nhập hoạt động thuần được báo cáo cho ngân hàng.",
     "derived from the seven net operating-income components reported in the bank statement",
    )
   elif (
    isinstance(existing_revenue,(int,float))
    and isinstance(item.get("bank_net_interest_income"),(int,float))
    and abs(existing_revenue-item["bank_net_interest_income"])<=max(abs(existing_revenue)*0.001,1000)
    and any(isinstance(item.get(field),(int,float)) and item[field]!=0 for field in bank_components[1:])
   ):
    # Clear a known legacy error: total operating income duplicated net interest income.
    prior.setdefault("revenue",existing_revenue)
    rejected_values.setdefault("revenue",{
     "value":existing_revenue,
     "reason":"legacy parser mapped net interest income into total bank operating income",
    })
    item.pop("revenue",None)
    item.pop("revenue_calculation",None)
    fields.discard("revenue")
    rejected.add("revenue")
    notes.append("Doanh thu cũ trùng thu nhập lãi thuần nhưng chưa đủ cấu phần để tái lập tổng thu nhập hoạt động; đã ẩn.")

   # PPOP = total operating income - reported operating expenses.
   op_expense=item.get("bank_operating_expenses")
   if (
    isinstance(item.get("revenue"),(int,float))
    and isinstance(op_expense,(int,float))
    and not ({"revenue","bank_operating_expenses"} & unquarterized)
    and not ({"revenue","bank_operating_expenses"} & rejected)
   ):
    derived_ppop=item["revenue"]-abs(op_expense)
    set_derived(
     "bank_pre_provision_operating_profit",derived_ppop,
     "Tổng thu nhập hoạt động - |chi phí hoạt động| theo BCTC ngân hàng.",
     "derived from total operating income minus operating expense",
    )

   # PBT = PPOP - positive credit-provision expense. Derive only when both
   # the quarterly PPOP and the snapshot's reported PBT are available.
   ppop=item.get("bank_pre_provision_operating_profit")
   pbt=item.get("pretax_profit")
   if isinstance(ppop,(int,float)) and isinstance(pbt,(int,float)):
    derived_provision=int(round(ppop-pbt))
    set_derived(
     "bank_provision_expense",derived_provision,
     "Lợi nhuận trước dự phòng - lợi nhuận trước thuế; chi phí dự phòng ghi dương như BCTC.",
     "derived from reconciled pre-provision operating profit minus reported quarterly PBT",
    )

   ppop=item.get("bank_pre_provision_operating_profit")
   provision=item.get("bank_provision_expense")
   pbt=item.get("pretax_profit")
   if all(isinstance(value,(int,float)) for value in (ppop,provision,pbt)):
    implied_pbt=ppop-abs(provision)
    tolerance=max(abs(pbt)*0.02,1000)
    if abs(implied_pbt-pbt)>tolerance:
     for field in ("bank_pre_provision_operating_profit","bank_provision_expense"):
      if isinstance(item.get(field),(int,float)):
       rejected_values.setdefault(field,{"value":item[field],"reason":"bank PPOP minus positive provision expense does not reconcile to reported PBT"})
       item.pop(field,None)
       item.pop(field+"_calculation",None)
       fields.discard(field)
       rejected.add(field)
       period_changed=True; changed_fields+=1
     notes.append("Lợi nhuận trước dự phòng và chi phí dự phòng OCR không khớp lợi nhuận trước thuế; hai chỉ tiêu chi tiết được ẩn.")

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

  # Operating + investing + financing cash flows reconcile to net cash change.
  # FX translation is separate and is used only in the cash-balance bridge.
  operating=item.get("operating_cash_flow")
  investing=item.get("investing_cash_flow")
  financing=item.get("financing_cash_flow")
  net_change=item.get("net_cash_change")
  fx=item.get("foreign_exchange_effect",0)
  if all(isinstance(v,(int,float)) for v in (operating,investing,financing,net_change)) and isinstance(fx,(int,float)):
   total=operating+investing+financing
   scale=max(abs(operating)+abs(investing)+abs(financing),abs(net_change),1000)
   if abs(total-net_change)>max(scale*0.05,1000):
    reject("operating_cash_flow","investing_cash_flow","financing_cash_flow",
           "net_cash_change","capital_expenditure","dividends_paid",
           "operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd",
           "net_cash_change_ytd","capital_expenditure_ytd",
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
   fx=item.get("foreign_exchange_effect",0)
   if abs((end-begin)-(net_change+(fx if isinstance(fx,(int,float)) else 0)))>tolerance:
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
  report_type_text=str(item.get("report_type") or "")
  if item.get("financial_line_items_status") and item.get("financial_line_items_schema_version") != DETAIL_SCHEMA_VERSION:
   item["financial_line_items_schema_version"]=DETAIL_SCHEMA_VERSION
   item["financial_line_items_schema_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True
  source_norm=norm(item.get("source_url") or "")
  source_index=str(item.get("source_index_url") or "")
  sync_scope_verified=(
   item.get("financial_line_items_source")==item.get("source_url")
   and "finance.vietstock.vn/" in source_index
   and "doctype=1" in source_index
  )
  # The direct quarterly worker accepts only consolidated records from this
  # catalog; preserve that scope explicitly even when the PDF filename omits it.
  if (sync_scope_verified or "hopnhat" in source_norm or "consolidated" in source_norm) and "hop nhat" not in norm(report_type_text):
   if report_type_text.lower().startswith("bctc "):
    item["report_type"]="BCTC hợp nhất "+report_type_text[5:]
   else:
    item["report_type"]=f"BCTC hợp nhất {symbol} {item.get('period')} ({report_type_text})"
   changed=True
  archive_source=resolve_archive_source(item,symbol)
  if archive_source and item.get("source_archive_file")!=archive_source:
   item["source_archive_file"]=archive_source
   item["source_archive_match"]="matched_report_queue_url"
   changed=True
  pages=load_report_pages(item,symbol)
  if not pages: continue

  # Count an extraction retry only when the source text evidence for this
  # quarter changes. This script runs on every one-report OCR pass; without
  # this fingerprint, all pending quarters would burn through the retry limit
  # even when their PDF text had not changed.
  page_evidence=[
   {
    "page":page.get("page"),
    "text":str(page.get("text") or ""),
    "ocr":page.get("ocr"),
    "extraction_method":page.get("extraction_method"),
   }
   for page in pages if isinstance(page,dict)
  ]
  evidence_payload=json.dumps(
   {"source_archive_file":str(item.get("source_archive_file") or ""),
    "pages":page_evidence},
   ensure_ascii=False,sort_keys=True,separators=(",",":")
  ).encode("utf-8")
  evidence_fingerprint=hashlib.sha256(evidence_payload).hexdigest()
  previous_fingerprint=str(item.get("core_financial_extraction_evidence_fingerprint") or "")
  evidence_changed=bool(previous_fingerprint and previous_fingerprint!=evidence_fingerprint)
  source_validation=item.get("source_validation")
  if not isinstance(source_validation,dict):
   source_validation={}
  explicitly_exhausted=source_validation.get("automatic_extraction_exhausted") is True

  if not previous_fingerprint:
   # Legacy attempt counters were incremented by repeated enrich passes, not
   # necessarily by distinct source revisions. Establish a baseline and reset
   # only those legacy manual-review states that lack an explicit source-level
   # exhaustion marker. Missing numbers remain blank until reconciled.
   item["core_financial_extraction_evidence_fingerprint"]=evidence_fingerprint
   item["core_financial_extraction_evidence_attempt_count"]=0
   if item.get("verification_status")=="manual_review_required_pending_extraction" and not explicitly_exhausted:
    item["verification_status"]="auto_pending_extraction"
    item["core_financial_extraction_status"]="auto_pending_extraction"
    item["core_financial_extraction_note"]="Đặt lại bộ đếm thử cũ chưa gắn với phiên bản nguồn; chỉ tính lượt mới khi nội dung nguồn thay đổi. Số liệu chưa đủ vẫn cần đối chiếu báo cáo."
   changed=True
  elif evidence_changed:
   item["core_financial_extraction_evidence_fingerprint"]=evidence_fingerprint
   if item.get("core_financial_extraction_manual_terminal") is True and not explicitly_exhausted:
    item.pop("core_financial_extraction_manual_terminal",None)
    item["core_financial_extraction_evidence_attempt_count"]=0
    item["verification_status"]="auto_pending_extraction"
    item["core_financial_extraction_status"]="auto_pending_extraction"
   elif item.get("verification_status")=="manual_review_required_pending_extraction" and not explicitly_exhausted:
    item["verification_status"]="auto_pending_extraction"
    item["core_financial_extraction_status"]="auto_pending_extraction"
   changed=True

  found=extract_fields(item,symbol,pages)
  mode=cumulative_income_mode(item,pages)
  found,withheld_fields=apply_quarter_scope(item,items,found,symbol,mode)
  core_found=extract_core_fields(item,symbol,pages,found,mode)
  core_calculations=core_found.pop("__core_calculations",{})
  core_pages=core_found.pop("__core_pages",[])
  core_new_fields=[]
  for field,value in core_found.items():
   if field=="revenue":
    continue
   if item.get(field) is None:
    item[field]=value
    core_new_fields.append(field)
  if core_new_fields:
   previous_fields=set(item.get("core_financial_extracted_fields") or [])
   item["core_financial_extracted_fields"]=sorted(previous_fields|set(core_new_fields))
   item["core_financial_extraction_source"]=str(item.get("source_archive_file") or "")
   item["core_financial_extraction_pages"]=core_pages
   item["core_financial_extraction_status"]="auto_extracted_pending_visual_review"
   item["core_financial_extraction_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   item["core_financial_extraction_note"]="Chỉ tiêu lõi được trích xuất từ văn bản PDF/ZIP đã lưu; chưa xác minh thủ công trên bản PDF."
   if core_calculations:
    item["core_financial_extraction_calculations"]=core_calculations
   changed=True
   quarter_count+=1
   field_count+=len(core_new_fields)
  core_required_ok=all(
   isinstance(item.get(field),(int,float))
   for field in ("total_assets","total_liabilities","equity","pretax_profit","net_profit")
  )
  core_balance_ok=(
   core_required_ok
   and abs(item["total_assets"]-item["total_liabilities"]-item["equity"])<=3
  )
  if core_balance_ok and item.get("verification_status") in {"auto_pending_extraction","manual_review_required_pending_extraction"}:
   item.pop("core_financial_extraction_manual_terminal",None)
   item["verification_status"]="auto_extracted_pending_visual_review"
   item["core_financial_extraction_status"]="auto_extracted_pending_visual_review"
   item["core_financial_extracted_fields"]=sorted(set(item.get("core_financial_extracted_fields") or [])|{
    "total_assets","total_liabilities","equity","pretax_profit","net_profit"
   })
   item["core_financial_extraction_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   item["verification_status_note"]="Các chỉ tiêu lõi đã được trích xuất tự động từ BCTC hợp nhất VietstockFinance; cần đối chiếu trực quan trước khi coi là xác minh."
   changed=True
   quarter_count+=1
   field_count+=1
  elif not core_required_ok and item.get("verification_status") in {"auto_pending_extraction","manual_review_required_pending_extraction"} and evidence_changed:
   # A retry is meaningful only after a new version of this quarter's page text
   # arrives (for example, after another OCR pass). Do not increment on every
   # run merely because this ticker still has some missing values.
   attempts=int(item.get("core_financial_extraction_evidence_attempt_count") or 0)+1
   item["core_financial_extraction_evidence_attempt_count"]=attempts
   item["core_financial_extraction_attempt_count"]=attempts
   item["core_financial_extraction_status"]="auto_pending_extraction"
   item["core_financial_extraction_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True
   field_count+=1
   if attempts>=3:
    item["verification_status"]="manual_review_required_pending_extraction"
    item["core_financial_extraction_status"]="manual_review_required_pending_extraction"
    item["core_financial_extraction_note"]="Đã thử trên ba phiên bản nội dung nguồn khác nhau nhưng chưa đủ bộ chỉ tiêu lõi khớp phương trình cân đối; giữ trống trường không đáng tin và yêu cầu rà soát PDF."
    quarter_count+=1
  if withheld_fields:
   pending=set(item.get("financial_line_items_unquarterized_fields") or [])
   pending.update(withheld_fields)
   item["financial_line_items_unquarterized_fields"]=sorted(pending)
   note="Một số chỉ tiêu thu nhập đang là số lũy kế; chưa đủ dữ liệu chi tiết các quý trước để tách riêng quý nên được để trống, không hiển thị số lũy kế như số quý."
   current_note=str(item.get("financial_line_items_note") or "")
   if note not in current_note:
    item["financial_line_items_note"]=(current_note+" "+note).strip()
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True; quarter_count+=1; field_count+=len(withheld_fields)
  if not found:
   if not item.get("financial_line_items_status"):
    item["financial_line_items_status"]="no_detail_fields_matched_pending_manual_review"
    item["financial_line_items_extracted_fields"]=[]
    item["financial_line_items_source"]=str(item.get("source_archive_file") or "")
    item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    item["financial_line_items_note"]="Không nhận diện chắc chắn được chỉ tiêu chi tiết từ văn bản đã lưu; giữ trống và cần đối chiếu báo cáo gốc."
    changed=True; quarter_count+=1; field_count+=1
   continue
  suppressed=set(item.get("financial_line_items_rejected_fields") or [])
  for key in list(found):
   if not key.startswith("__") and key in suppressed:
    found.pop(key,None)
  if not found: continue
  found,rejected=sane_fields(item,found,symbol)
  rejection_changed=False
  if rejected:
   print(f"{path.name if 'path' in locals() else symbol} {item.get('period')}: skipped implausible extracted values {','.join(rejected)}")
   prior_rejected=set(item.get("financial_line_items_rejected_fields") or [])
   fresh_rejected=set(rejected)-prior_rejected
   if fresh_rejected:
    item["financial_line_items_rejected_fields"]=sorted(prior_rejected|set(rejected))
    item["financial_line_items_rejected_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    note="Một số chỉ tiêu bị giữ trống vì không vượt qua kiểm tra cân đối kế toán hoặc đối chiếu chéo; xem danh sách trường bị loại."
    current_note=str(item.get("financial_line_items_note") or "")
    if note not in current_note:
     item["financial_line_items_note"]=(current_note+" "+note).strip()
    changed=True
    field_count+=len(fresh_rejected)
    rejection_changed=True
  if not found:
   if rejection_changed: quarter_count+=1
   continue
  new_fields=[]
  for field,value in found.items():
   if field.startswith("__"): continue
   if item.get(field) is None:
    item[field]=value; new_fields.append(field)
   elif (
    symbol in BANKS
    and field in {"bank_customer_loans","bank_net_service_income","operating_cash_flow_ytd","financing_cash_flow_ytd","cash_beginning","cash_ending"}
    and field in set(item.get("financial_line_items_extracted_fields") or [])
    and isinstance(item.get(field),(int,float))
    and item.get(field)!=value
   ):
    old_value=item[field]
    item.setdefault("financial_line_items_prior_values",{}).setdefault(field,old_value)
    reasons={
     "bank_customer_loans":"Reparsed from the compactly OCRed main customer-loan subtotal row (net loan balance), not the gross-loan detail row.",
     "bank_net_service_income":"Reparsed from the explicit net service income/loss row, not an adjacent row captured as service expense.",
     "operating_cash_flow_ytd":"Reparsed from net operating cash flow after changes in operating assets and liabilities, not the subtotal before working-capital changes.",
     "financing_cash_flow_ytd":"Reparsed from the explicit net financing cash-flow row in the bank B04/TCTD statement.",
     "cash_beginning":"Reparsed from the explicit opening cash balance row in the bank B04/TCTD statement.",
     "cash_ending":"Reparsed from the explicit closing cash balance row in the bank B04/TCTD statement.",
    }
    item.setdefault("financial_line_items_value_corrections",{})[field]={
     "previous_value":old_value,"new_value":value,"reason":reasons[field]
    }
    item[field]=value
    new_fields.append(field)
   elif (
    field in set(item.get("financial_line_items_extracted_fields") or [])
    and str(item.get("financial_line_items_status") or "").startswith("auto_extracted")
    and scale_mismatch(item.get(field),value)
   ):
    old_value=item[field]
    item.setdefault("financial_line_items_prior_values",{}).setdefault(field,old_value)
    item.setdefault("financial_line_items_value_corrections",{})[field]={
     "previous_value":old_value,
     "new_value":value,
     "reason":"reparsed with corrected VND unit scale after detecting an OCR-corrupted statement unit header",
    }
    item[field]=value
    new_fields.append(field)
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
  if symbol in BANKS and isinstance(found.get("bank_net_service_income"),(int,float)):
   old_service_expense=item.get("bank_service_expense")
   explicit_net_service=found["bank_net_service_income"]
   if (
    isinstance(old_service_expense,(int,float))
    and old_service_expense==explicit_net_service
    and "bank_service_expense" in set(item.get("financial_line_items_extracted_fields") or [])
    and "bank_service_expense" not in found
   ):
    item.setdefault("financial_line_items_prior_values",{}).setdefault("bank_service_expense",old_service_expense)
    item.setdefault("financial_line_items_value_corrections",{})["bank_service_expense"]={
     "previous_value":old_service_expense,
     "new_value":None,
     "reason":"Previous OCR parser captured the adjacent net-service-income row as service expense; the report does not clearly disclose the expense amount on that row."
    }
    item.pop("bank_service_expense",None)
    old_fields=set(item.get("financial_line_items_extracted_fields") or [])
    old_fields.discard("bank_service_expense")
    item["financial_line_items_extracted_fields"]=sorted(old_fields)
    item["financial_line_items_note"]=(str(item.get("financial_line_items_note") or "")+" Chi phí dịch vụ được để trống do giá trị cũ bị nhận nhầm từ dòng lãi thuần dịch vụ.").strip()
    changed=True; field_count+=1
  basis=found.get("__cashflow_period_basis")
  if basis and item.get("cashflow_period_basis")!=basis:
   item["cashflow_period_basis"]=basis; new_fields.append("cashflow_period_basis")
  if new_fields:
   fields=set(item.get("financial_line_items_extracted_fields") or [])
   fields.update(new_fields)
   item["financial_line_items_extracted_fields"]=sorted(fields)
   item["financial_line_items_status"]="auto_extracted_pending_visual_review"
   item["financial_line_items_schema_version"]=DETAIL_SCHEMA_VERSION
   item["financial_line_items_schema_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   item["financial_line_items_source"]=str(item.get("source_archive_file") or "")
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   base_note=str(item.get("financial_line_items_note") or "")
   generic_note="Trích xuất từ văn bản PDF/ZIP đã lưu; cần đối chiếu trực quan với báo cáo gốc."
   if generic_note not in base_note:
    item["financial_line_items_note"]=(base_note+" "+generic_note).strip()
   changed=True
   if not rejection_changed: quarter_count+=1
   field_count+=len(new_fields)
  elif rejection_changed:
   quarter_count+=1

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
 symbol=str(__import__("os").environ.get("FINANCIAL_ENRICH_SYMBOL", "")).strip().upper()
 if not re.fullmatch(r"[A-Z0-9]{2,10}", symbol):
  print("No valid FINANCIAL_ENRICH_SYMBOL; skip rather than process multiple tickers in one run.")
  return 0
 path=DATA / f"financials-{symbol}.json"
 if not path.is_file():
  print(f"No quarterly snapshot for selected ticker {symbol}; nothing to enrich.")
  return 0
 try:
  changed,quarters,fields=enrich_snapshot(path)
  if changed:
   print(f"{path.name}: {quarters} quarter(s) enriched/marked for review, {fields} field updates")
  else:
   print(f"{path.name}: no further safe detail fields found.")
 except Exception as exc:
  print(f"::warning::{path.name}: {exc}")
 return 0

if __name__=="__main__":
 raise SystemExit(main())
