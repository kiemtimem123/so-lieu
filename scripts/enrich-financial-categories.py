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
# The checkpoint helper uses the same detail schema so completed extraction
# does not loop forever on quarters already reprocessed with the note-code guards.
DETAIL_SCHEMA_VERSION = "2026-10-27-other-statements-source-fields-v11"
CORE_EXTRACTION_PARSER_VERSION = "2026-10-23-ngan-vnd-unit-v2-statement-rows"
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
 "bank_cash_on_hand":["tien mat, vang bac, da quy","tien mat vang bac da quy","tien mat, vang","tien mat vang"],
 "bank_deposits_at_state_bank":["tien gui tai nhnn","tien gui tai ngan hang nha nuoc"],
 "bank_deposits_and_loans_to_credit_institutions":["tien gui va cho vay cac tctd khac","tien gui va cho vay cac to chuc tin dung khac","tien gui va cap tin dung cho cac tctd khac","tien gui va cap tin dung cho cac to chuc tin dung khac","tien, vang gui va cho vay cac to chuc tin dung","tien, vang gui va cho vay cac tctd khac","tien vang gui va cho vay cac to chuc tin dung khac","tien vang gui va cho vay cac tctd khac"],
 "bank_customer_loans":["cho vay khach hang","cho vay khichhing","chovaykhachhang","cho vay khach hang tong"],
 "bank_trading_securities":["chung khoan kinh doanh"],
 "bank_derivatives_and_other_financial_assets":["cac cong cu tai chinh phai sinh va cac tai san tai chinh khac"],
 "bank_investment_securities":["chung khoan dau tu"],
 "bank_contributions_and_long_term_investments":["gop von, dau tu dai han","gop von dau tu dai han"],
 "bank_other_assets":["tai san co khac"],
 "bank_deposits_and_borrowings_from_credit_institutions":["tien gui va tien vay cac tctd khac","tien gui va vay cac tctd khac","tien gui va vay cac to chuc tin dung khac","tien gui va vay cac to chuc tai chinh cac tctd khac"],
 "bank_customer_deposits":["tien gui cua khach hang"],
 "bank_valuable_papers":["phat hanh giay to co gia"],
 "bank_funding_and_trust_liabilities":["von tai tro, uy thac dau tu"],
 "bank_other_liabilities":["cac khoan no khac","cac khoan ng khac","cac khoan ngkhac","cac khoan ngkhc"],
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
 "net_profit_attributable":["loi nhuan sau thue cua co dong cong ty me","loi nhuan sau thue cua co dong cua cong ty me","loi nhuan thuoc ve co dong cong ty me","loi nhuan thuan co dong ngan hang","loi nhuan thuan cua co dong cua"],
}
BANK_INCOME_LABELS = {
 "bank_interest_income":["thu nhap lai va cac khoan thu nhap tuong tu"],
 "bank_interest_expense":["chi phi lai va cac khoan chi phi tuong tu"],
 "bank_net_interest_income":["thu nhap thuan tu lai","thu nhap lai thuan"],
 "bank_service_income":["thu nhap tu hoat dong dich vu"],
 "bank_service_expense":["chi phi hoat dong dich vu"],
 "bank_net_service_income":["lai/lo thuan tu hoat dong dich vu","lai lo thuan tu hoat dong dich vu","lai thuan tu hoat dong dich vu"],
 "bank_fx_net_income":["lai thuan tu hoat dong kinh doanh ngoai hoi"],
 "bank_trading_securities_net":["lai thuan tu mua ban chung khoan kinh doanh","lai/(lo) thuan tu mua ban chung khoan kinh doanh","lai lo thuan tu mua ban chung khoan kinh doanh"],
 "bank_investment_securities_net":["lai thuan tu mua ban chung khoan dau tu","lai thuan tu mua ban chung khoan dau tu va gop von dau tu dai han"],
 "bank_other_operating_net":["lai thuan tu hoat dong kinh doanh khac","lai thuan tu hoat dong khac"],
 "bank_dividend_and_capital_income":["thu nhap tu gop von, mua co phan"],
 "bank_operating_expenses":["tong chi phi hoat dong","chi phi hoat dong"],
 "bank_pre_provision_operating_profit":["loi nhuan thuan tu hoat dong kinh doanh truoc chi phi du phong rui ro"],
 "bank_provision_expense":["chi phi du phong rui ro"],
 "bank_non_controlling_profit":["loi ich cua co dong khong kiem soat"],
}
CASHFLOW_LABELS = {
 "operating_cash_flow_ytd":["luu chuyen tien thuan su dung vao hoat dong kinh doanh","luu chuyen tien thuan (su dung vao)/tu hoat dong kinh doanh","luu chuyen tien thuan su dung vao/tu hoat dong kinh doanh","luu chuyen tien thuan tu/(su dung vao) hoat dong kinh doanh","luu chuyen tien thuan tu hoat dong kinh doanh","luu chuyen tien tu hoat dong kinh doanh"],
 "investing_cash_flow_ytd":["luu chuyen tien thuan su dung vao hoat dong dau tu","luu chuyen tien thuan su dung trong hoat dong dau tu","luu chuyen tien thuan tu/(su dung vao) hoat dong dau tu","luu chuyen tien thuan su dung vao/tu hoat dong dau tu","luu chuyen tien thuan tu hoat dong dau tu","luu chuyen tien tu hoat dong dau tu"],
 "financing_cash_flow_ytd":["luu chuyen tien thuan tu/(su dung vao) hoat dong tai chinh","luu chuyen tien thuan (su dung vao)/tu hoat dong tai chinh","luu chuyen tien thuan tu hoat dong tai chinh","luu chuyen tien thuan tu hoat dong taichinh","luu chuyen tien thuan tu hoat dong taichinn","luu chuyen tien tu hoat dong tai chinh"],
 "capital_expenditure_ytd":["tien chi de mua sam xay dung tai san co dinh","tien chi mua sam xay dung tai san co dinh","mua sam tai san co dinh","mua sam xay dung tai san co dinh va cac tai san dai han khac"],
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
 # Company-form B01a-DN/HN statements can OCR "Đổi" as "Đột" or "B01a" as "BO1a".
 # Use the official form code plus a balance-sheet total as a strong fallback.
 if any(term in text for term in ("bang can doi ke toan","bang can dot ke toan","statement of financial position","balance sheet")):
  return "balance"
 if (
  re.search(r"\bb[0o]?1[a-z]?\s*[-/]?\s*dn(?:/hn)?\b",text)
  and any(term in text for term in ("tong cong tai san","tong cong nguon von","total assets","total liabilities"))
 ):
  return "balance"
 if (
  re.search(r"\bb[0o]?2[a-z]?\s*[-/]?\s*dn(?:/hn)?\b",text)
  and any(term in text for term in ("doanh thu","loi nhuan","revenue","profit before tax"))
 ):
  return "income"
 if (
  re.search(r"\bb[0o]?3[a-z]?\s*[-/]?\s*dn(?:/hn)?\b",text)
  and any(term in text for term in ("luu chuyen tien te","cash flow"))
 ):
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
 if any(t in header for t in ("ngan dong","ngan vnd","nghin dong","nghin vnd","thousand dong","thousand vnd")) or re.search(r"\bngh?[a-z~._-]{0,4}n\s+(?:dong|vnd)\b",header): return 0.001
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

def strip_leading_note_reference(text):
 # Vietstock note references can be misread as Roman numerals, digits, or
 # mixed OCR tokens such as III.18, 11.18, 111.20, IIH.48, or 1H.18.
 # Remove the entire reference before parsing, then preserve the first/current
 # column only; this is intentionally independent of the following numbers.
 raw=str(text or "")
 return re.sub(r"^\s*[A-Za-z0-9]{1,6}\s*\.\s*\d{1,2}\s+", " ", raw, count=1, flags=re.IGNORECASE)


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
     tail=strip_leading_note_reference(combined[position+len(target):])
     # A dash in the first (current) period must not shift a comparative value.
     if re.match(r"^\s*[-–—](?:\s|$)",tail): return 0
     vals=amounts(tail,threshold=threshold)
     if vals: return int(round(vals[0]*factor))
 return None


def value_by_label_with_note_reference(pages, labels, factor):
 # Some bank income lines (notably income from capital contributions and shares)
 # are legitimately below VND 1,000 million. The generic parser suppresses small
 # values to avoid reading note numbers as amounts, so parse the statement row
 # explicitly and discard the leading note reference when a row has three cells.
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
     tail=strip_leading_note_reference(combined[position+len(target):])
     if re.match(r"^\s*[-–—](?:\s|$)",tail): return 0
     vals=[]
     for token in NUMBER_RE.findall(tail):
      parsed=parse_amount(token)
      if parsed is not None and not (1900 <= abs(parsed) <= 2100):
       vals.append(parsed)
     if len(vals)>=3 and 1<=abs(vals[0])<=99:
      vals=vals[1:]
     if vals:
      return int(round(vals[0]*factor))
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

def select_report_page_payload(item,symbol):
 source=str(item.get("source_archive_file") or "").strip()
 if not source: return None
 file=(ROOT/source).resolve()
 try: file.relative_to(RAW.resolve())
 except ValueError: return None
 extracted=file.with_suffix(file.suffix+".extracted.json")
 if not extracted.is_file(): return None
 try: payload=json.loads(extracted.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError): return None
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
   candidates.append((score,member))
 direct=get_pages(payload)
 if direct:
  direct_text=norm(" ".join(str(p.get("text",""))[:1000] for p in direct[:10]))
  score=min(len(direct),10)+(2 if "bao cao tai chinh" in direct_text or "financial statement" in direct_text else 0)
  candidates.append((score,payload))
 if not candidates: return None
 candidates.sort(key=lambda pair:pair[0],reverse=True)
 return candidates[0][1]


def load_report_pages(item,symbol):
 selected=select_report_page_payload(item,symbol)
 return get_pages(selected) if selected else []


def core_extraction_pages_complete(item,symbol,pages,max_pages=14):
 """True only when the selected source PDF has every page in the OCR target range."""
 selected=select_report_page_payload(item,symbol)
 if not isinstance(selected,dict): return False
 try:
  page_count=int(selected.get("page_count") or 0)
 except (TypeError,ValueError):
  page_count=0
 target_count=min(max(page_count,0),max(1,int(max_pages)))
 if target_count<1: return False
 existing={
  int(page.get("page")) for page in pages
  if isinstance(page,dict) and str(page.get("page","")).isdigit()
 }
 return all(number in existing for number in range(1,target_count+1))

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
  any(term in text for term in (
   "trieu dong","trieu vnd","million vnd","ngan dong","ngan vnd",
   "nghin dong","nghin vnd","thousand dong","thousand vnd","don vi tinh trieu"
  ))
  or re.search(r"\bngh?[a-z~._-]{0,4}n\s+(?:dong|vnd)\b",text)
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
   if (
    any(term in line for term in (
     "trieu dong","trieu vnd","million vnd","ngan dong","ngan vnd",
     "nghin dong","nghin vnd","thousand dong","thousand vnd"
    ))
    or re.search(r"\bngh?[a-z~._-]{0,4}n\s+(?:dong|vnd)\b",line)
   ) and (
    ("don vi" in line) or ("unit" in line) or "%" in line
    or any(term in line for term in ("ngan dong","ngan vnd","nghin dong","nghin vnd","thousand dong","thousand vnd"))
   )
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
    r"^\s*[,;:._\-\x60~]*\s*(?:\|\s*)?(?:tong\s*)?(?:cong\s*)?tai\s*san\s*co(?:\s|$)",
    r"^\s*[,;:._\-\x60~]*\s*(?:\|\s*)?(?:tong\s*)?(?:cong\s*)?tai\s*san(?:\s|$)",
    r"^\s*[,;:._\-\x60~]*\s*(?:\|\s*)?total\s*assets(?:\s|$)"
   ],factor
  )

 equity_labels=[
  "tong cong von chu so huu","tong von chu so huu","von chu so huu","total equity",
  "owners' equity","owners’ equity","owner's equity",
  "shareholders' equity","shareholders’ equity","shareholders equity",
  "total owners' equity","total shareholders' equity"
 ]
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
  # Keep the values in both balance-sheet columns for a strict same-column
  # match: OCR may merge a digit into the current source total or convert a
  # thousands separator to "/", while the comparative column remains intact.
  asset_column_values=[]
  total_asset_patterns=[
   re.compile(r"^\s*[,;:._\-\x60~]*\s*(?:\|\s*)?(?:tong\s*)?(?:cong\s*)?tai\s*san\s*co(?:\s|$)"),
   re.compile(r"^\s*[,;:._\-\x60~]*\s*(?:\|\s*)?(?:tong\s*)?(?:cong\s*)?tai\s*san(?:\s|$)"),
   re.compile(r"^\s*[,;:._\-\x60~]*\s*(?:\|\s*)?total\s*assets(?:\s|$)"),
  ]
  if isinstance(assets,(int,float)):
   row_tolerance=max(abs(assets)*0.00001,1000)
   for page in balance:
    for asset_line in str(page.get("text","")).splitlines():
     asset_clean=norm(asset_line)
     if not any(pattern.search(asset_clean) for pattern in total_asset_patterns):
      continue
     values=[int(round(value*factor)) for value in amounts(asset_line,threshold=1000)]
     if values and abs(values[0]-assets)<=row_tolerance:
      asset_column_values=values
      break
    if asset_column_values:
     break
   if not asset_column_values:
    asset_column_values=[int(round(assets))]

  # Don't require a perfectly OCRed "Tổng nợ phải trả" label. The hard gate
  # is that the source-total row has "vốn chủ sở hữu" and its values match
  # total-assets values in the same column(s). Normalize slash separators
  # inside numbers, for example "2/300,868/728" -> "2,300,868,728".
  for page in balance:
   lines=str(page.get("text","")).splitlines()
   for index,line in enumerate(lines):
    clean_window=norm(" ".join(lines[index:index+3]))
    if "von chu so" not in clean_window:
     continue
    candidate_lines=[line]
    if not amounts(re.sub(r"(?<=\d)/(?=\d)",",",line),threshold=1000):
     for lookahead in range(index+1,min(index+4,len(lines))):
      if is_statement_row_start(lines[lookahead]):
       break
      candidate_lines.append(lines[lookahead])
      if amounts(re.sub(r"(?<=\d)/(?=\d)",",",lines[lookahead]),threshold=1000):
       break
    row_values=[]
    for candidate_line in candidate_lines:
     parsed=amounts(re.sub(r"(?<=\d)/(?=\d)",",",candidate_line),threshold=1000)
     if parsed:
      row_values=parsed
      break
    if not row_values or not asset_column_values:
     continue
    source_values=[int(round(value*factor)) for value in row_values]
    matched_column=None
    for column,(source_value,asset_value) in enumerate(zip(source_values,asset_column_values)):
     compare_tolerance=max(abs(asset_value)*0.00001,1000)
     if abs(source_value-asset_value)<=compare_tolerance:
      matched_column=column
      break
    if matched_column is not None:
     source_total=int(round(assets))
     calculations["source_total_match"]="Source-total row matches total-assets row in column %d after OCR separator normalization" % (matched_column+1)
     break
   if source_total is not None and isinstance(assets,(int,float)) and abs(source_total-assets)<=max(abs(assets)*0.00001,1000):
    break
 liabilities=value_by_label(
  balance,["tong cong no phai tra","tong no phai tra","total liabilities"],factor,
  exclude_terms=["von chu so huu","liabilities and equity"]
 ) if balance else None
 if balance:
  # On broker B01-CTCK/HN reports, the explicit aggregate row uses code
  # "C. Nợ phải trả". Prefer that row unconditionally when present: some OCR
  # outputs split/garble the following "and equity" words in the total-sources
  # row, which can make a broad "Tổng nợ phải trả" substring capture total
  # assets plus equity instead of liabilities.
  coded_liabilities=value_by_row_prefix(
   balance,[
    r"^\s*(?:\|\s*)?\d{1,3}\s*\|\s*c\.?\s*no\s+phai\s+tra(?:\s|$)",
    r"^\s*(?:\|\s*)?c\.?\s+no\s+phai\s+tra(?:\s|$)",
    r"^\s*(?:\|\s*)?\d{1,3}\s*\|\s*c\.?\s*liabilities(?:\s|$)",
    r"^\s*(?:\|\s*)?c\.?\s*liabilities(?:\s|$)",
    r"^\s*(?:\|\s*)?\d{1,3}\s*\|\s*c\.?\s*total\s+liabilities(?:\s|$)",
   ],factor
  )
  if isinstance(coded_liabilities,(int,float)):
   liabilities=coded_liabilities

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
 # Standard Vietnamese income statement codes are stable even when OCR wraps the words
 # "trước thuế"/"sau thuế" after the numeric columns.
 if pbt is None and profit_pages:
  pbt=value_by_row_prefix(
   profit_pages,[r"^\s*(?:\|\s*)?50\s*(?:\||\s)"],factor
  )
 if net is None and profit_pages:
  net=value_by_row_prefix(
   profit_pages,[r"^\s*(?:\|\s*)?60\s*(?:\||\s)"],factor
  )
 if pbt is not None:
  out["pretax_profit"]=pbt
 if net is not None:
  out["net_profit"]=net
 parent_profit=value_by_label(
  profit_pages,
  ["loi nhuan thuan co dong ngan hang","loi nhuan thuan cua co dong cua",
   "loi nhuan sau thue cua co dong cong ty me",
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


def extract_bank_split_column_income(pages, factor):
 """Recover a bank income statement when OCR serializes the current-period value column separately.

 Some Vietstock PDFs extract all labels first, then all figures in visual column
 order. In that case label matching cannot pair the rows. Only accept the known
 22-row bank income layout when the figures are one-per-line; interleaved
 multi-column lines are rejected rather than guessed.
 """
 expected_fields = [
  "bank_interest_income", "bank_interest_expense", "bank_net_interest_income",
  "bank_service_income", "bank_service_expense", "bank_net_service_income",
  "bank_fx_net_income", "bank_trading_securities_net",
  "bank_investment_securities_net", "bank_other_operating_net",
  "bank_dividend_and_capital_income", "revenue", "bank_operating_expenses",
  "bank_pre_provision_operating_profit", "bank_provision_expense",
  "pretax_profit", "income_tax_current", "income_tax_deferred", "income_tax",
  "net_profit", "bank_non_controlling_profit", "net_profit_attributable",
 ]
 for page in pages:
  lines=str(page.get("text","")).splitlines()
  normalized=norm(" ".join(lines))
  # These are already selected as income-statement pages by extract_fields();
  # avoid a second heading test because OCR often corrupts the title line.
  marker=next((idx for idx,line in enumerate(lines) if "so phat sinh quy" in norm(line)),None)
  if marker is None:
   continue
  values=[]
  for line in lines[marker+1:]:
   clean=norm(line)
   if "luy ke tu dau nam" in clean or "luy ke tu" in clean:
    break
   parsed=amounts(line,threshold=1000)
   if len(parsed)>1:
    values=[]
    break
   if parsed:
    values.extend(parsed)
    if len(values)>=len(expected_fields):
     break
  if len(values)!=len(expected_fields):
   continue
  values=[int(round(value*factor)) for value in values]
  mapped=dict(zip(expected_fields,values))
  # Expense totals are shown as positive amounts elsewhere in the dashboard;
  # component expense rows retain the sign printed in the source statement.
  for key in ("bank_operating_expenses","bank_provision_expense","income_tax"):
   mapped[key]=abs(mapped[key])
  return mapped
 return {}


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
   # "Các khoản nợ khác" is a total. Do not match its child line
   # "Dự phòng các khoản nợ khác" just because the shorter label is contained.
   if field=="bank_other_liabilities":
    val=value_by_label(bal,labels,scale,exclude_terms=["du phong cac khoan no khac"])
   else:
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
   elif field=="bank_dividend_and_capital_income":
    val=value_by_label_with_note_reference(inc,labels,scale)
   else:
    val=value_by_label(inc,labels,scale)
   if val is not None: out[field]=val
  # Fall back to the explicit statement-column order only if OCR has separated
  # all labels from the numeric value columns. Never overwrite a value parsed
  # from a paired row, and never accept multi-value/interleaved lines here.
  for field,value in extract_bank_split_column_income(inc,scale).items():
   if field not in out:
    out[field]=value
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
   or re.search(r"\btu ngay 0?1 thang 0?1 nam 20\d{2}\b",cft)
   or re.search(r"\bgiai doan tai chinh tu ngay 0?1 thang 0?1 nam 20\d{2}\b",cft)
   or re.search(r"\b(?:cho )?ky(?: ke toan)? (?:6|9|12|sau|chin|muoi hai) thang ket thuc ngay\b",cft)
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
 # Process chronologically so a restored quarter-end cash balance can safely
 # become the next quarter's opening balance.
 period_items={
  str(candidate.get("period") or ""):candidate
  for candidate in items
  if isinstance(candidate,dict) and re.fullmatch(r"20\d{2}-Q[1-4]",str(candidate.get("period") or ""))
 }
 ordered_items=sorted(
  items,
  key=lambda candidate:str(candidate.get("period") or "") if isinstance(candidate,dict) else ""
 )
 for item in ordered_items:
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

   # Store bank expense magnitudes as positive values for consistent reconciliation,
   # even when the PDF prints the expense in parentheses.
   operating_expense_value=item.get("bank_operating_expenses")
   if isinstance(operating_expense_value,(int,float)) and operating_expense_value<0:
    item.setdefault("financial_line_items_prior_values",{}).setdefault("bank_operating_expenses",operating_expense_value)
    item.setdefault("financial_line_items_value_corrections",{})["bank_operating_expenses"]={"previous_value":operating_expense_value,"new_value":abs(int(round(operating_expense_value))),"reason":"Normalized bank operating expenses to the positive expense convention used in subtotal reconciliation."}
    item["bank_operating_expenses"]=abs(int(round(operating_expense_value)))
    fields.add("bank_operating_expenses")
    rejected.discard("bank_operating_expenses")
    rejected_values.pop("bank_operating_expenses",None)
    period_changed=True; changed_fields+=1

   provision_value=item.get("bank_provision_expense")
   if isinstance(provision_value,(int,float)) and provision_value<0:
    item.setdefault("financial_line_items_prior_values",{}).setdefault("bank_provision_expense",provision_value)
    item.setdefault("financial_line_items_value_corrections",{})["bank_provision_expense"]={
     "previous_value":provision_value,
     "new_value":abs(int(round(provision_value))),
     "reason":"Normalized the report's parenthesized credit-provision expense to the positive expense convention used throughout bank-category calculations."
    }
    item["bank_provision_expense"]=abs(int(round(provision_value)))
    fields.add("bank_provision_expense")
    rejected.discard("bank_provision_expense")
    rejected_values.pop("bank_provision_expense",None)
    period_changed=True; changed_fields+=1

   interest_income=item.get("bank_interest_income")
   interest_expense=item.get("bank_interest_expense")
   net_interest=item.get("bank_net_interest_income")
   # If OCR gross interest income contradicts the independently reported net-interest subtotal,
   # reconcile to reported net interest plus the expense row and preserve the correction record.
   if (
    isinstance(interest_income,(int,float)) and isinstance(interest_expense,(int,float))
    and isinstance(net_interest,(int,float))
    and not ({"bank_interest_income","bank_interest_expense","bank_net_interest_income"} & unquarterized)
   ):
    expected_interest_income=int(round(net_interest+abs(interest_expense)))
    difference=expected_interest_income-interest_income
    if difference and abs(difference)<=max(abs(interest_income)*0.15,1000):
     set_derived(
      "bank_interest_income",expected_interest_income,
      "Thu nhập lãi = thu nhập lãi thuần + chi phí lãi; đối chiếu tổng phụ BCTC ngân hàng.",
      "Corrected OCR gross interest income to reported net-interest income plus interest expense."
     )
     interest_income=expected_interest_income
   if (
    isinstance(interest_income,(int,float)) and isinstance(interest_expense,(int,float))
    and not ({"bank_interest_income","bank_interest_expense"} & unquarterized)
   ):
    set_derived(
     "bank_net_interest_income",interest_income-abs(interest_expense),
     "Thu nhập lãi - |chi phí lãi| theo BCTC ngân hàng.",
     "derived from reported interest income minus reported interest expense"
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

   # Reconcile a small capital-contribution OCR digit error only when all seven bank income components exist.
   component_values=[item.get(field) for field in bank_components]
   components_safe=(all(isinstance(value,(int,float)) for value in component_values)
    and not (set(bank_components) & unquarterized) and not (set(bank_components) & rejected))
   capital_value=item.get("bank_dividend_and_capital_income")
   if components_safe and isinstance(item.get("revenue"),(int,float)) and isinstance(capital_value,(int,float)) and abs(capital_value)<=10000:
    component_delta=int(round(item["revenue"]-sum(component_values)))
    if component_delta and abs(component_delta)<=10000:
     set_derived("bank_dividend_and_capital_income",capital_value+component_delta,
      "Thu nhập góp vốn/mua cổ phần được đối chiếu để tổng các cấu phần bằng tổng thu nhập hoạt động đã công bố.",
      "Reconciled a small OCR digit error in capital-contribution income to reported operating income after checking the other six components.")

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

   # PBT = PPOP - positive credit-provision expense. Prefer a reported PPOP;
   # if it is missing, rebuild it from the reported PBT and normalized expense.
   ppop=item.get("bank_pre_provision_operating_profit")
   pbt=item.get("pretax_profit")
   provision=item.get("bank_provision_expense")
   if isinstance(ppop,(int,float)) and isinstance(pbt,(int,float)):
    derived_provision=int(round(ppop-pbt))
    set_derived(
     "bank_provision_expense",derived_provision,
     "Lợi nhuận trước dự phòng - lợi nhuận trước thuế; chi phí dự phòng ghi dương như BCTC.",
     "derived from reconciled pre-provision operating profit minus reported quarterly PBT",
    )
   elif not isinstance(ppop,(int,float)) and isinstance(pbt,(int,float)) and isinstance(provision,(int,float)) and provision>=0:
    set_derived(
     "bank_pre_provision_operating_profit",pbt+provision,
     "Lợi nhuận trước thuế + chi phí dự phòng tín dụng dương; khôi phục tổng phụ trước dự phòng.",
     "derived from reported quarterly PBT plus normalized positive provision expense",
    )

   ppop=item.get("bank_pre_provision_operating_profit")
   revenue=item.get("revenue")
   op_expense=item.get("bank_operating_expenses")
   if isinstance(ppop,(int,float)) and isinstance(revenue,(int,float)) and not isinstance(op_expense,(int,float)):
    derived_op_expense=int(round(revenue-ppop))
    if derived_op_expense>=0:
     set_derived(
      "bank_operating_expenses",derived_op_expense,
      "Tổng thu nhập hoạt động - lợi nhuận trước dự phòng; chi phí hoạt động lưu dương.",
      "derived from reported total operating income minus reconciled pre-provision operating profit",
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

  # Recover missing bank subtotals only from matching figures in the same
  # reported quarter. Never derive when any participating field is unquarterized,
  # explicitly rejected, or the source report scope is still flagged for review.
  if symbol in BANKS:
   unquarterized=set(item.get("financial_line_items_unquarterized_fields") or [])
   source_validation=item.get("source_validation") if isinstance(item.get("source_validation"),dict) else {}
   scope_blocked=source_validation.get("scope_validation_required") is True
   interest_income=item.get("bank_interest_income")
   interest_expense=item.get("bank_interest_expense")
   net_interest=item.get("bank_net_interest_income")
   if not scope_blocked:
    if (
     isinstance(interest_income,(int,float))
     and isinstance(net_interest,(int,float))
     and not isinstance(interest_expense,(int,float))
     and not ({"bank_interest_income","bank_net_interest_income","bank_interest_expense"} & unquarterized)
     and not ({"bank_interest_income","bank_net_interest_income"} & rejected)
    ):
     derived_expense=int(round(interest_income-net_interest))
     if derived_expense>=0:
      set_derived(
       "bank_interest_expense",-derived_expense,
       "Chi phí lãi = −(thu nhập lãi − thu nhập lãi thuần) theo ba dòng cùng kỳ của BCTC ngân hàng.",
       "derived missing interest expense from same-quarter reported interest income and net interest income",
      )
    elif (
     isinstance(interest_expense,(int,float))
     and isinstance(net_interest,(int,float))
     and not isinstance(interest_income,(int,float))
     and not ({"bank_interest_income","bank_net_interest_income","bank_interest_expense"} & unquarterized)
     and not ({"bank_net_interest_income","bank_interest_expense"} & rejected)
    ):
     derived_income=int(round(net_interest+abs(interest_expense)))
     if derived_income>=0:
      set_derived(
       "bank_interest_income",derived_income,
       "Thu nhập lãi = thu nhập lãi thuần + |chi phí lãi| theo ba dòng cùng kỳ của BCTC ngân hàng.",
       "derived missing gross interest income from same-quarter reported net interest income and interest expense",
      )

    ppop=item.get("bank_pre_provision_operating_profit")
    generic_op=item.get("operating_profit")
    if (
     isinstance(ppop,(int,float))
     and not isinstance(generic_op,(int,float))
     and "bank_pre_provision_operating_profit" not in unquarterized
     and "bank_pre_provision_operating_profit" not in rejected
    ):
     set_derived(
      "operating_profit",int(round(ppop)),
      "Lợi nhuận hoạt động chung của ngân hàng lấy từ dòng lợi nhuận thuần trước chi phí dự phòng rủi ro tín dụng trong cùng BCTC.",
      "mirrored the reported bank pre-provision operating-profit subtotal into the generic operating-profit metric",
     )

    consolidated_net=item.get("net_profit")
    parent_net=item.get("net_profit_attributable")
    minority=item.get("bank_non_controlling_profit")
    if (
     isinstance(consolidated_net,(int,float))
     and isinstance(parent_net,(int,float))
     and (
      not isinstance(minority,(int,float))
      or int(round(minority))!=int(round(consolidated_net-parent_net))
     )
     and "bank_non_controlling_profit" not in set(item.get("financial_line_items_manually_verified_fields") or [])
     and not ({"net_profit","net_profit_attributable","bank_non_controlling_profit"} & unquarterized)
     and not ({"net_profit","net_profit_attributable"} & rejected)
    ):
     set_derived(
      "bank_non_controlling_profit",int(round(consolidated_net-parent_net)),
      "Lợi nhuận cổ đông không kiểm soát = lợi nhuận sau thuế hợp nhất − lợi nhuận sau thuế thuộc cổ đông ngân hàng mẹ.",
      "derived non-controlling profit from consolidated net profit minus net profit attributable to parent",
     )

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

  # DPG Q2 2026 has a known OCR digit substitution in the net-sales row.
  # Apply the correction only when the archived source text itself contains the
  # matching reported value; preserve the prior value and the evidence note.
  if symbol == "DPG" and item.get("period") == "2026-Q2":
   archive_rel=str(item.get("source_archive_file") or "").strip()
   sidecar_path=(ROOT / (archive_rel + ".extracted.json")) if archive_rel else None
   try:
    sidecar=json.loads(sidecar_path.read_text(encoding="utf-8")) if sidecar_path and sidecar_path.is_file() else {}
   except (OSError,json.JSONDecodeError):
    sidecar={}
   source_text=" ".join(
    str(page.get("text") or "")
    for page in (sidecar.get("pages") or [])
    if isinstance(page,dict)
   )
   reported_net_sales=re.search(r"net sales.{0,120}?1[.,]858[.,]764[.,]986[.,][sS5]89",source_text,re.I)
   if reported_net_sales and item.get("revenue") != 1858765:
    previous_revenue=item.get("revenue")
    if isinstance(previous_revenue,(int,float)):
     prior.setdefault("revenue",previous_revenue)
    item["revenue"]=1858765
    item["revenue_calculation"]="Doanh thu thuần 1.858.764.986.589 VND từ dòng Net sales trang 10 của PDF hợp nhất DPG Q2/2026; quy đổi sang triệu VND."
    item["financial_line_items_revenue_reconciliation"]={
     "previous_value":previous_revenue,
     "reconstructed_value":1858765,
     "formula":"reported net sales from archived source text / 1,000,000",
     "source_archive_file":archive_rel,
     "source_page":10,
     "evidence_pattern":"Net sales ... 1.858.764.986.S89",
    }
    fields.add("revenue")
    rejected.discard("revenue")
    rejected_values.pop("revenue",None)
    notes.append("Doanh thu DPG Q2/2026 được sửa theo dòng Net sales trang 10 của PDF lưu trữ; giá trị OCR cũ bị đánh dấu sai.")
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

  # Normalize YTD statement rows to standalone-quarter values before reconciliation.
  # Do not use values that remain explicitly rejected by source/scope validation.
  if (
   str(item.get("cashflow_period_basis") or "")=="year_to_date"
   and not (
    isinstance(item.get("source_validation"),dict)
    and item.get("source_validation",{}).get("scope_validation_required") is True
   )
  ):
   period_match=re.fullmatch(r"(20\d{2})-Q([1-4])",str(item.get("period") or ""))
   if period_match:
    year=int(period_match.group(1)); quarter=int(period_match.group(2))
    previous_period=f"{year}-Q{quarter-1}" if quarter>1 else f"{year-1}-Q4"
    previous_item=period_items.get(previous_period)
    previous_rejected=set(previous_item.get("financial_line_items_rejected_fields") or []) if isinstance(previous_item,dict) else set()

    # Q1 equals its own YTD total. Q2-Q4 equal current YTD less prior-quarter YTD.
    for quarter_field,ytd_field in CASHFLOW_QUARTER_FROM_YTD.items():
     current_ytd=item.get(ytd_field)
     if (
      not isinstance(current_ytd,(int,float))
      or ytd_field in rejected
     ):
      continue
     if quarter==1:
      expected=int(round(current_ytd))
     else:
      prior_ytd=previous_item.get(ytd_field) if isinstance(previous_item,dict) else None
      if (
       not isinstance(prior_ytd,(int,float))
       or ytd_field in previous_rejected
      ):
       continue
      expected=int(round(current_ytd-prior_ytd))

     old_value=item.get(quarter_field)
     old_rejected=rejected_values.get(quarter_field)
     needs_update=(
      not isinstance(old_value,(int,float))
      or int(round(old_value))!=expected
      or quarter_field in rejected
     )
     if needs_update:
      prior_value=old_value if isinstance(old_value,(int,float)) else (
       old_rejected.get("value") if isinstance(old_rejected,dict) else None
      )
      if isinstance(prior_value,(int,float)) and int(round(prior_value))!=expected:
       prior.setdefault(quarter_field,prior_value)
       item.setdefault("financial_line_items_value_corrections",{})[quarter_field]={
        "previous_value":prior_value,
        "new_value":expected,
        "reason":f"Normalized YTD {ytd_field} to standalone {quarter_field} using {item.get('period')} minus {previous_period if quarter>1 else 'no prior quarter'}.",
       }
      item[quarter_field]=expected
      item[quarter_field+"_calculation"]=(
       f"{quarter_field} quý I = giá trị lũy kế quý I ({ytd_field})."
       if quarter==1 else
       f"{quarter_field} quý riêng = {ytd_field} kỳ hiện tại − {ytd_field} của {previous_period}."
      )
      fields.add(quarter_field)
      rejected.discard(quarter_field)
      rejected_values.pop(quarter_field,None)
      period_changed=True; changed_fields+=1

    # Cash-flow statements show year-opening cash on Q2-Q4 forms; normalize
    # dashboard opening cash to the previous quarter close.
    reported_begin=item.get("cash_beginning_reported_ytd")
    if quarter==1 and isinstance(reported_begin,(int,float)) and "cash_beginning_reported_ytd" not in rejected:
     expected_begin=int(round(reported_begin))
    else:
     prior_close=previous_item.get("cash_ending") if isinstance(previous_item,dict) else None
     if not isinstance(prior_close,(int,float)) and isinstance(previous_item,dict):
      prior_close=previous_item.get("cash_ending_reported_ytd")
     expected_begin=int(round(prior_close)) if isinstance(prior_close,(int,float)) else None
    if isinstance(expected_begin,(int,float)):
     old_begin=item.get("cash_beginning")
     if "cash_beginning" in rejected or not isinstance(old_begin,(int,float)) or int(round(old_begin))!=expected_begin:
      if isinstance(old_begin,(int,float)) and int(round(old_begin))!=expected_begin:
       prior.setdefault("cash_beginning",old_begin)
      elif isinstance(rejected_values.get("cash_beginning"),dict):
       old_rejected_begin=rejected_values["cash_beginning"].get("value")
       if isinstance(old_rejected_begin,(int,float)):
        prior.setdefault("cash_beginning",old_rejected_begin)
      item["cash_beginning"]=expected_begin
      item["cash_beginning_calculation"]=(
       "Số dư tiền đầu quý bằng tiền cuối quý liền trước."
       if quarter>1 else
       "Số dư tiền đầu quý I lấy từ dòng tiền và tương đương tiền đầu kỳ trên BCTC VietstockFinance."
      )
      fields.add("cash_beginning")
      rejected.discard("cash_beginning")
      rejected_values.pop("cash_beginning",None)
      period_changed=True; changed_fields+=1

    reported_end=item.get("cash_ending_reported_ytd")
    if isinstance(reported_end,(int,float)) and "cash_ending_reported_ytd" not in rejected:
     expected_end=int(round(reported_end))
    else:
     current_end=item.get("cash_ending")
     expected_end=int(round(current_end)) if isinstance(current_end,(int,float)) and "cash_ending" not in rejected else None
    if isinstance(expected_end,(int,float)):
     old_end=item.get("cash_ending")
     if "cash_ending" in rejected or not isinstance(old_end,(int,float)) or int(round(old_end))!=expected_end:
      if isinstance(old_end,(int,float)) and int(round(old_end))!=expected_end:
       prior.setdefault("cash_ending",old_end)
      elif isinstance(rejected_values.get("cash_ending"),dict):
       old_rejected_end=rejected_values["cash_ending"].get("value")
       if isinstance(old_rejected_end,(int,float)):
        prior.setdefault("cash_ending",old_rejected_end)
      item["cash_ending"]=expected_end
      item["cash_ending_calculation"]="Số dư tiền cuối quý lấy từ dòng tiền và tương đương tiền cuối kỳ trong báo cáo VietstockFinance."
      fields.add("cash_ending")
      rejected.discard("cash_ending")
      rejected_values.pop("cash_ending",None)
      period_changed=True; changed_fields+=1

    # Preserve the cash-balance bridge for future data-quality audits.
    opening=item.get("cash_beginning"); closing=item.get("cash_ending")
    quarter_net=item.get("net_cash_change")
    fx=item.get("foreign_exchange_effect",0)
    if isinstance(fx,(int,float)) and all(isinstance(v,(int,float)) for v in (opening,closing,quarter_net)):
     bridge=int(round(closing-opening-quarter_net-fx))
     recovery={
      "basis":"year_to_date_report_normalized_to_quarter",
      "period":item.get("period"),
      "cash_beginning":int(round(opening)),
      "cash_ending_reported":int(round(closing)),
      "quarter_net_cash_change":int(round(quarter_net)),
      "quarter_foreign_exchange_effect":int(round(fx)),
      "closing_balance_less_opening_net_cash_change_and_fx":bridge,
      "source_index_url":item.get("source_index_url"),
      "source_document_url":item.get("source_url"),
      "source_archive_file":item.get("source_archive_file"),
     }
     if item.get("cashflow_balance_bridge_recovery")!=recovery:
      item["cashflow_balance_bridge_recovery"]=recovery
      period_changed=True; changed_fields+=1

  # For securities brokers, the official statement's total operating revenue
  # is the comparable revenue metric. Generic label matching can accidentally
  # read a nearby financial-income row into item["revenue"]. If the broker's
  # explicitly extracted total is available from the same quarterly report,
  # align the generic revenue field to it and preserve the superseded OCR value.
  if symbol in BROKERS:
   broker_revenue=item.get("broker_total_operating_revenue")
   current_revenue=item.get("revenue")
   scope_info=item.get("source_validation")
   if not isinstance(scope_info,dict):
    scope_info={}
   if (
    isinstance(broker_revenue,(int,float))
    and not isinstance(broker_revenue,bool)
    and __import__("math").isfinite(broker_revenue)
    and scope_info.get("scope_validation_required") is not True
    and (
     not isinstance(current_revenue,(int,float))
     or isinstance(current_revenue,bool)
     or abs(current_revenue-broker_revenue)>max(abs(broker_revenue)*0.001,1000)
    )
   ):
    if isinstance(current_revenue,(int,float)) and not isinstance(current_revenue,bool):
     prior.setdefault("revenue",current_revenue)
    item.setdefault("financial_line_items_value_corrections",{})["revenue"]={
     "previous_value":current_revenue,
     "new_value":broker_revenue,
     "reason":"Generic revenue parse disagreed with total operating revenue explicitly extracted from the same VietstockFinance CTCK statement; use the reported broker operating-revenue total.",
     "source_index_url":item.get("source_index_url"),
     "source_url":item.get("source_url"),
     "source_archive_file":item.get("source_archive_file"),
    }
    item["revenue"]=broker_revenue
    item["revenue_calculation"]="Đồng bộ với tổng doanh thu hoạt động được trích xuất trực tiếp từ cùng kỳ BCTC công ty chứng khoán VietstockFinance; không dùng dòng doanh thu tài chính làm doanh thu chính."
    fields.add("revenue")
    rejected.discard("revenue")
    rejected_values.pop("revenue",None)
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
  elif item.get("financial_line_items_rejected_fields"):
   item["financial_line_items_rejected_fields"]=[]
   period_changed=True
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



def repair_tcx_2026_source_rows(items,symbol):
 """Reconcile TCX 2026 quarter cash flows and Q3 statement rows against archived Vietstock PDFs.

 The CTCK cash-flow statement is cumulative YTD while the income statement has
 separate quarterly and YTD columns. A legacy OCR pass confused PBT with OCF,
 capex with net investing flow, and a single advisory-revenue row with total
 operating revenue. Apply these narrowly scoped repairs only when the archived
 source pages contain the expected reported amounts.
 """
 if symbol!="TCX":
  return False,0,0
 by_period={
  str(item.get("period") or ""):item
  for item in items if isinstance(item,dict) and item.get("period")
 }
 changed=False
 quarter_count=0
 field_count=0

 def archived_pages(item):
  archive_rel=str(item.get("source_archive_file") or "").strip()
  if not archive_rel:
   return {}
  sidecar=ROOT/(archive_rel+".extracted.json")
  try:
   payload=json.loads(sidecar.read_text(encoding="utf-8"))
  except (OSError,json.JSONDecodeError):
   payload={}
  if not isinstance(payload,dict):
   return {}
  documents=[]
  if payload.get("kind")=="pdf":
   documents=[payload]
  elif payload.get("kind")=="zip":
   documents=[
    member for member in payload.get("members",[])
    if isinstance(member,dict) and member.get("kind")=="pdf"
   ]
  result={}
  for document in documents:
   for page in document.get("pages",[]):
    if not isinstance(page,dict): continue
    try:
     page_num=int(page.get("page"))
    except (TypeError,ValueError):
     continue
    result.setdefault(page_num,[])
    result[page_num].append(str(page.get("text") or ""))
  return {number:" ".join(parts) for number,parts in result.items()}

 def record_value(item,field,value,reason):
  nonlocal changed,field_count
  previous=item.get(field)
  if previous==value:
   return
  if isinstance(previous,(int,float)) and not isinstance(previous,bool):
   item.setdefault("financial_line_items_prior_values",{}).setdefault(field,previous)
  item.setdefault("financial_line_items_value_corrections",{})[field]={
   "previous_value":previous,"new_value":value,"reason":reason
  }
  item[field]=value
  changed=True
  field_count+=1

 # Q1/2024 source reconciliation: read explicit Quý I B02a-CTCK rows from
 # the archived VietstockFinance PDF. Keep row 24 (combined provision/impairment
 # and lending-cost line) in the total but do not mislabel it as pure interest.
 q1_2024=by_period.get("2024-Q1")
 if isinstance(q1_2024,dict):
  q1_pages=archived_pages(q1_2024)
  q1_income_tokens={
   9:[
    "633.894.391.116","26.819.346.924","572.607.934.798","68.014.797.084",
    "145.712.853.246","211.688.437.189","12.145.172.612","21.534.999.999",
    "1.183.086.304","1.693.601.019.272","34.453.346.343","3.'183.666.s13",
    "63.843.348.722","10.569.839.226","39.232.071.770","151.282.272.574"
   ],
   10:[
    "6.147.640.648","271.458.788.515","262.319.802.326",
    "116.669.265.433","1.160.338.333.398","18.843.093",
    "231.957.680.000","231.112.619.703","845.060.297","928.361.810.305"
   ],
  }
  q1_income_ok=bool(q1_pages) and all(
   all(token in q1_pages.get(page,"") for token in tokens)
   for page,tokens in q1_income_tokens.items()
  )
  if q1_income_ok:
   q1_income_values={
    "revenue":1693601.019272,
    "broker_total_operating_revenue":1693601.019272,
    "broker_fvtpl_gain":633894.391116,
    "broker_held_to_maturity_income":26819.346924,
    "broker_lending_income":572607.934798,
    "broker_afs_income":68014.797084,
    "broker_brokerage_revenue":145712.853246,
    "broker_underwriting_revenue":211688.437189,
    "broker_custody_revenue":12145.172612,
    "broker_financial_advisory_revenue":21534.999999,
    "broker_other_operating_income":1183.086304,
    "broker_fvtpl_loss":34453.346343,
    "broker_brokerage_expense":63843.348722,
    "broker_custody_expense":10569.839226,
    "broker_other_operating_expense":39232.071770,
    "broker_total_operating_expenses":151282.272574,
    "broker_operating_expenses":151282.272574,
    "financial_income":6147.640648,
    "broker_financial_income":6147.640648,
    "financial_expense":271458.788515,
    "broker_financial_expense":271458.788515,
    "interest_expense":262319.802326,
    "broker_interest_expense":262319.802326,
    "admin_expense":116669.265433,
    "broker_admin_expenses":116669.265433,
    "operating_profit":1160338.333398,
    "broker_net_operating_profit":1160338.333398,
    "income_tax":231957.680000,
    "income_tax_current":231112.619703,
    "income_tax_deferred":845.060297,
   }
   q1_before_fields=field_count
   for field,value in q1_income_values.items():
    record_value(
     q1_2024,field,value,
     "Source-backed correction from the archived VietstockFinance B02a-CTCK statement; Q1/2024, "
     f"PDF page {10 if field in {'financial_income','broker_financial_income','financial_expense','broker_financial_expense','interest_expense','broker_interest_expense','admin_expense','broker_admin_expenses','operating_profit','broker_net_operating_profit','income_tax','income_tax_current','income_tax_deferred'} else 9}. "
     "Current-quarter VND row divided by 1,000,000."
    )
   q1_fields_before=set(q1_2024.get("financial_line_items_extracted_fields") or [])
   q1_fields_after=q1_fields_before|set(q1_income_values)
   if q1_fields_after!=q1_fields_before:
    q1_2024["financial_line_items_extracted_fields"]=sorted(q1_fields_after)
    changed=True; field_count+=1
   q1_rejected_before=set(q1_2024.get("financial_line_items_rejected_fields") or [])
   q1_rejected_after=q1_rejected_before-set(q1_income_values)
   if q1_rejected_after!=q1_rejected_before:
    q1_2024["financial_line_items_rejected_fields"]=sorted(q1_rejected_after)
    changed=True; field_count+=1
   q1_rejected_values=q1_2024.get("financial_line_items_rejected_values")
   if isinstance(q1_rejected_values,dict):
    for field in q1_income_values:
     q1_rejected_values.pop(field,None)
   q1_income_evidence={
    "source_policy":"VietstockFinance document catalog and linked PDF only",
    "source_index_url":q1_2024.get("source_index_url"),
    "source_document_url":q1_2024.get("source_url"),
    "source_archive_file":q1_2024.get("source_archive_file"),
    "report_form":"B02a-CTCK",
    "report_scope":"standalone securities-company financial statement; not consolidated",
    "pdf_pages":[9,10],
    "manually_visual_reviewed":True,
    "exact_source_vnd":{field:int(round(value*1000000)) for field,value in q1_income_values.items()},
    "note":"Total operating revenue and expense components were read from the explicit three-month statement. The combined row 24 remains in total operating expenses but is not relabelled as pure borrowing expense."
   }
   if q1_2024.get("financial_line_items_source_row_reconciliation")!=q1_income_evidence:
    q1_2024["financial_line_items_source_row_reconciliation"]=q1_income_evidence
    changed=True; field_count+=1
   q1_note=(
    "Đã đối chiếu trực quan B02a-CTCK VietstockFinance Q1/2024, PDF trang 9–10: sửa tổng doanh thu hoạt động, "
    "các dòng doanh thu/chi phí, lợi nhuận hoạt động, thuế và tổng chi phí theo cột quý I. "
    "Dòng chi phí số 24 gồm nhiều khoản tổng hợp nên không gán nhầm thành riêng chi phí lãi vay."
   )
   q1_old_note=str(q1_2024.get("financial_line_items_note") or "")
   if q1_note not in q1_old_note:
    q1_2024["financial_line_items_note"]=(q1_old_note+" "+q1_note).strip()
    changed=True; field_count+=1
   if field_count>q1_before_fields:
    q1_2024["financial_line_items_status"]="auto_extracted_pending_visual_review"
    q1_2024["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed=True; quarter_count+=1
  else:
   print("TCX 2024-Q1: income repair skipped; required B02a-CTCK source tokens did not match.")

 # Balance-sheet recovery for TCX Q1/Q2 2024. These B01a-CTCK values are
 # standalone company balances, and every accepted field has a source-page
 # trail. Totals already stored in the core snapshot remain unchanged/rounded.
 balance_specs={
  "2024-Q1":{
   "evidence":{
    5:["47.184.524.962.757","44.026.431.030.982","3.158.093.931.775","19.838.888.765.755","19.152.369.771.965","2.077.862.639.126","2.352.046.000.000","350.224.486.597","58.067.296.618"],
    6:["21.911.875.104.076","720.055.351.262","24.552.594.507.419","13.205.484.229.760","20.850.129.455.475","81.102.357.029","714.047.369.s49"],
   },
   "values":{
    "current_assets":44026431.030982,
    "non_current_assets":3158093.931775,
    "broker_held_to_maturity_assets":2352046.000000,
    "broker_lending_assets":19838888.765755,
    "broker_afs_assets":19152369.771965,
    "broker_receivables":350224.486597,
    "fixed_assets":58067.296618,
    "current_liabilities":21911875.104076,
    "long_term_liabilities":720055.351262,
    "broker_short_term_borrowings":20850129.455475,
    "broker_short_term_bonds":81102.357029,
    "broker_long_term_bonds":714047.369549,
    "retained_earnings":13205484.229760,
   },
   "pages":[5,6],
  },
  "2024-Q2":{
   "evidence":{
    5:["52.021.362.358.734","48.861.579.413.303","3.159.782.945.431","24.693.764.239.854","18.783.067.451.386","2.775.473.279.243","1.851.105.785.348","435.100.224.522","52.570.661.540"],
    6:["24.777.335.661.227","2.600.724.459.312","24.643.302.238.195","13.306.899.085.123","22.348.574.457.637","90.365.281.510","2.596.279.942.814"],
   },
   "values":{
    "current_assets":48861579.413303,
    "non_current_assets":3159782.945431,
    "broker_held_to_maturity_assets":1851105.785348,
    "broker_lending_assets":24693764.239854,
    "broker_afs_assets":18783067.451386,
    "broker_receivables":435100.224522,
    "fixed_assets":52570.661540,
    "current_liabilities":24777335.661227,
    "long_term_liabilities":2600724.459312,
    "broker_short_term_borrowings":22348574.457637,
    "broker_short_term_bonds":90365.281510,
    "broker_long_term_bonds":2596279.942814,
    "retained_earnings":13306899.085123,
   },
   "pages":[5,6],
  },
  "2025-Q1":{
   # The OCR has a digit/transcription error in current assets on page 6.
   # Reconstruct it from the reported total liabilities + equity on page 7,
   # less the reported non-current-assets subtotal on page 6.
   "evidence":{
    6:["52.968,968.277.078","3,374,594,808,902"],
    7:["29.034.864.968.810","27.294.698.117.170","56.329.563.085.980"],
   },
   "values":{
    "current_assets":52954968.277078,
   },
   "pages":[6,7],
   "manually_visual_reviewed":False,
   "calculation":"(total liabilities + equity reported on page 7) - non-current assets reported on page 6; source OCR's current-assets row contains a digit mismatch.",
  },
  "2026-Q1":{
   "evidence":{
    6:["43.198.457.639.720","40.601.152.377.163","2.597.305.262.557"],
   },
   "values":{
    "current_liabilities":40601152.377163,
    "long_term_liabilities":2597305.262557,
   },
   "pages":[6],
   "manually_visual_reviewed":True,
  },
 }
 for period,spec in balance_specs.items():
  item=by_period.get(period)
  if not isinstance(item,dict):
   continue
  source=archived_pages(item)
  evidence_ok=bool(source) and all(
   all(token in source.get(page,"") for token in tokens)
   for page,tokens in spec["evidence"].items()
  )
  if not evidence_ok:
   print(f"TCX {period}: balance repair skipped; exact B01a-CTCK tokens did not match.")
   continue
  before_field_count=field_count
  for field,value in spec["values"].items():
   record_value(
    item,field,value,
    f"Re-read from the visually checked B01a-CTCK balance sheet linked by VietstockFinance, {period}, PDF page {5 if field in {'current_assets','non_current_assets','broker_held_to_maturity_assets','broker_lending_assets','broker_afs_assets','broker_receivables','fixed_assets'} else 6}; source VND divided by 1,000,000."
   )
  fields_before=set(item.get("financial_line_items_extracted_fields") or [])
  fields_after=fields_before|set(spec["values"])
  if fields_after!=fields_before:
   item["financial_line_items_extracted_fields"]=sorted(fields_after)
   changed=True; field_count+=1
  rejected_before=set(item.get("financial_line_items_rejected_fields") or [])
  rejected_after=rejected_before-set(spec["values"])
  if rejected_after!=rejected_before:
   item["financial_line_items_rejected_fields"]=sorted(rejected_after)
   changed=True; field_count+=1
  rejected_values=item.get("financial_line_items_rejected_values")
  if isinstance(rejected_values,dict):
   for field in spec["values"]:
    rejected_values.pop(field,None)
  balance_evidence={
   "source_policy":"VietstockFinance document catalog and linked PDF only",
   "source_index_url":item.get("source_index_url"),
   "source_document_url":item.get("source_url"),
   "source_archive_file":item.get("source_archive_file"),
   "report_form":"B01a-CTCK",
   "report_scope":"standalone securities-company balance sheet; not consolidated",
   "pdf_pages":spec["pages"],
   "manually_visual_reviewed":bool(spec.get("manually_visual_reviewed",True)),
   "fields":{field:{"value_million_vnd":value,"source_value_vnd":int(round(value*1000000))} for field,value in spec["values"].items()},
  }
  if item.get("financial_line_items_balance_source_reconciliation")!=balance_evidence:
   item["financial_line_items_balance_source_reconciliation"]=balance_evidence
   changed=True; field_count+=1
  if spec.get("manually_visual_reviewed",True):
   note=(
    f"Đã đối chiếu trực quan B01a-CTCK VietstockFinance {period}, PDF trang {','.join(str(p) for p in spec['pages'])}: "
    "khôi phục các dòng tài sản/nợ ngắn hạn, dài hạn và tổng phụ có căn cứ. Đây là báo cáo riêng CTCK, không phải báo cáo hợp nhất."
   )
  elif period=="2025-Q1":
   note=(
    "TCX 2025-Q1: hiệu chỉnh tài sản ngắn hạn thành 52.954.968,277078 triệu VND theo phương trình "
    "tổng nợ phải trả + vốn chủ sở hữu - tài sản dài hạn, vì dòng tài sản ngắn hạn bị OCR sai chữ số. "
    "Đối chiếu bằng văn bản PDF VietstockFinance trang 6–7; cần rà soát trực quan hình ảnh."
   )
  else:
   note=(
    f"TCX {period}: khôi phục các dòng nợ ngắn hạn/dài hạn từ B01a-CTCK VietstockFinance, "
    f"PDF trang {','.join(str(p) for p in spec['pages'])}; tổng hai khoản khớp tổng nợ phải trả."
   )
  old_note=str(item.get("financial_line_items_note") or "")
  if note not in old_note:
   item["financial_line_items_note"]=(old_note+" "+note).strip()
   changed=True; field_count+=1
  if field_count>before_field_count:
   item["financial_line_items_status"]="auto_extracted_pending_visual_review"
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True; quarter_count+=1

 # Repair TCX Q2/2024 where the older OCR parser mapped the foreign-exchange
 # row to generic revenue and mapped the finance-income subtotal to the broker's
 # total operating revenue. These exact values are guarded by the archived
 # VietstockFinance B02a-CTCK rows on PDF pages 9–11.
 q2_2024=by_period.get("2024-Q2")
 if isinstance(q2_2024,dict):
  page_text=archived_pages(q2_2024)
  required_tokens={
   9:[
    "696.861.698.381","30.229.481.127","637.279.350.434",
    "162.804.353.720","156.192.251.513","455.377.520.333",
    "12.332.762.027","81.675.699.999","863.260.127",
    "616.377.661","152.721.575.174","76.755.135.395",
    "10.777.990.296","42.114.053.438","22.286.356.185"
   ],
   10:["7.960.143.556","352.917.770.484","338.258.357.643","123.231.620.654","1.612.705.554.905"],
   11:["314.483.853.511","315.222.111.907","738.262.396","1.297.455.468.843"],
  }
  source_rows_ok=bool(page_text) and all(
   all(token in page_text.get(page,"") for token in tokens)
   for page,tokens in required_tokens.items()
  )
  if source_rows_ok:
   q2_start_field_count=field_count
   q2_start_status=str(q2_2024.get("financial_line_items_status") or "")
   q2_2024_values={
    "revenue":2233616.377661,
    "broker_total_operating_revenue":2233616.377661,
    "broker_fvtpl_gain":696861.698381,
    "broker_held_to_maturity_income":30229.481127,
    "broker_lending_income":637279.350434,
    "broker_afs_income":162804.353720,
    "broker_brokerage_revenue":156192.251513,
    "broker_underwriting_revenue":455377.520333,
    "broker_custody_revenue":12332.762027,
    "broker_financial_advisory_revenue":81675.699999,
    "broker_other_operating_income":863.260127,
    "broker_fvtpl_loss":22286.356185,
    "broker_brokerage_expense":76755.135395,
    "broker_custody_expense":10777.990296,
    "broker_other_operating_expense":42114.053438,
    "broker_total_operating_expenses":152721.575174,
    "broker_operating_expenses":152721.575174,
    "financial_income":7960.143556,
    "broker_financial_income":7960.143556,
    "financial_expense":352917.770484,
    "broker_financial_expense":352917.770484,
    "interest_expense":338258.357643,
    "broker_interest_expense":338258.357643,
    "admin_expense":123231.620654,
    "broker_admin_expenses":123231.620654,
    "operating_profit":1612705.554905,
    "broker_net_operating_profit":1612705.554905,
    "income_tax":314483.853511,
    "income_tax_current":315222.111907,
    "income_tax_deferred":-738.262396,
   }
   q2_source_pages={
    "revenue":9,"broker_total_operating_revenue":9,
    "broker_fvtpl_gain":9,"broker_held_to_maturity_income":9,"broker_lending_income":9,
    "broker_afs_income":9,"broker_brokerage_revenue":9,"broker_underwriting_revenue":9,
    "broker_custody_revenue":9,"broker_financial_advisory_revenue":9,
    "broker_other_operating_income":9,"broker_fvtpl_loss":9,"broker_brokerage_expense":9,
    "broker_custody_expense":9,"broker_other_operating_expense":9,
    "broker_total_operating_expenses":9,"broker_operating_expenses":9,
    "financial_income":10,"broker_financial_income":10,"financial_expense":10,
    "broker_financial_expense":10,"interest_expense":10,"broker_interest_expense":10,
    "admin_expense":10,"broker_admin_expenses":10,"operating_profit":10,
    "broker_net_operating_profit":10,"income_tax":11,"income_tax_current":11,
    "income_tax_deferred":11,
   }
   for field,value in q2_2024_values.items():
    record_value(
     q2_2024,field,value,
     f"Re-read and visually checked on the archived VietstockFinance B02a-CTCK statement, PDF page {q2_source_pages[field]}; value is from the current Q2 column and is scaled from VND to million VND."
    )
   detail_fields_before=set(q2_2024.get("financial_line_items_extracted_fields") or [])
   detail_fields_after=detail_fields_before|set(q2_2024_values)
   if detail_fields_after!=detail_fields_before:
    q2_2024["financial_line_items_extracted_fields"]=sorted(detail_fields_after)
    changed=True; field_count+=1
   rejected_fields_before=set(q2_2024.get("financial_line_items_rejected_fields") or [])
   rejected_fields_after=rejected_fields_before-set(q2_2024_values)
   if rejected_fields_after!=rejected_fields_before:
    q2_2024["financial_line_items_rejected_fields"]=sorted(rejected_fields_after)
    changed=True; field_count+=1
   rejected_values=q2_2024.get("financial_line_items_rejected_values")
   if isinstance(rejected_values,dict):
    rejected_values_before=dict(rejected_values)
    for field in q2_2024_values:
     rejected_values.pop(field,None)
    if rejected_values!=rejected_values_before:
     changed=True; field_count+=1
   visual_evidence={
    "source_policy":"VietstockFinance document catalog and linked PDF only",
    "source_index_url":q2_2024.get("source_index_url"),
    "source_document_url":q2_2024.get("source_url"),
    "source_archive_file":q2_2024.get("source_archive_file"),
    "report_form":"B02a-CTCK",
    "report_scope":"standalone securities-company financial statement; not consolidated",
    "pdf_pages":[9,10,11],
    "manually_visual_reviewed":True,
    "corrected_fields":sorted(q2_2024_values),
    "note":"The revenue fields previously matched the financial-income / exchange-difference rows. Replaced them with the reported total operating revenue and reconciled the financial-income, financial-expense, operating-profit and tax rows from the Q2 column."
   }
   if q2_2024.get("financial_line_items_source_row_reconciliation")!=visual_evidence:
    q2_2024["financial_line_items_source_row_reconciliation"]=visual_evidence
    changed=True; field_count+=1
   if q2_2024.get("financial_line_items_source_pages")!=[9,10,11]:
    q2_2024["financial_line_items_source_pages"]=[9,10,11]
    changed=True; field_count+=1
   note=(
    "Đã kiểm tra trực quan các dòng B02a-CTCK trên PDF VietstockFinance trang 9–11: "
    "tách lại tổng doanh thu hoạt động khỏi doanh thu tài chính; sửa doanh thu/chi phí tài chính, "
    "chi phí lãi vay, quản lý, lợi nhuận hoạt động và thuế theo cột Quý II. Đơn vị lưu là triệu VND. "
    "Tổng thuế lấy theo dòng công bố 314.483.853.511 VND; thuế hiện hành cộng thuế hoãn lại lệch 4.000 VND theo văn bản nguồn, nên giữ nguyên từng dòng báo cáo và lưu tổng thuế riêng."
   )
   old_note=str(q2_2024.get("financial_line_items_note") or "")
   if note not in old_note:
    q2_2024["financial_line_items_note"]=(old_note+" "+note).strip()
    changed=True; field_count+=1
   if q2_start_field_count<field_count or q2_start_status!="auto_extracted_pending_visual_review":
    q2_2024["financial_line_items_status"]="auto_extracted_pending_visual_review"
    q2_2024["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed=True
    quarter_count+=1
  else:
   print("TCX 2024-Q2: source-backed income repair skipped; required visual-source tokens did not all match.")

 # Recover TCX Q1/Q2 2024 cash flows from the exact B03a-CTCK YTD totals.
 # In the older OCR snapshot, the Q1 operating flow was mistakenly populated
 # with PBT and the opening cash was sometimes read from the client-custody
 # section. Keep the YTD values separately and derive standalone Q2 by deltas.
 cash_2024_specs={
  "2024-Q1":{
   "evidence":{
    11:["4.137.298.348.768","2.921.383.874"],
    12:["1.635.901.377.580","2.504.318.355.062","4.582.180.994.188","2.077.862.639.126"],
   },
   "values":{
    "operating_cash_flow_ytd":-4137298.348768,
    "investing_cash_flow_ytd":-2921.383874,
    "financing_cash_flow_ytd":1635901.377580,
    "net_cash_change_ytd":-2504318.355062,
    "operating_cash_flow":-4137298.348768,
    "investing_cash_flow":-2921.383874,
    "financing_cash_flow":1635901.377580,
    "net_cash_change":-2504318.355062,
    "capital_expenditure_ytd":-2921.383874,
    "capital_expenditure":-2921.383874,
    "cash_beginning_reported_ytd":4582180.994188,
    "cash_beginning":4582180.994188,
    "cash_ending":2077862.639126,
    "cash_and_equivalents":2077862.639126,
   },
   "pages":[11,12],
  },
  "2024-Q2":{
   "evidence":{
    12:["6.172.085.602.557","6.003.479.681"],
    13:["4.371.381.367.293","1.806.707.714.945","4.582.180.994.188","2.775.473.279.243"],
   },
   "values":{
    "operating_cash_flow_ytd":-6172085.602557,
    "investing_cash_flow_ytd":-6003.479681,
    "financing_cash_flow_ytd":4371381.367293,
    "net_cash_change_ytd":-1806707.714945,
    "operating_cash_flow":-2034787.253789,
    "investing_cash_flow":-3082.095807,
    "financing_cash_flow":2735479.989713,
    "net_cash_change":697610.640117,
    "capital_expenditure_ytd":-6003.479681,
    "capital_expenditure":-3082.095807,
    "cash_beginning_reported_ytd":4582180.994188,
    "cash_beginning":2077862.639126,
    "cash_ending":2775473.279243,
    "cash_and_equivalents":2775473.279243,
   },
   "pages":[12,13],
  },
 }
 for period,spec in cash_2024_specs.items():
  item=by_period.get(period)
  if not isinstance(item,dict):
   continue
  cash24_start_field_count=field_count
  cash24_start_status=str(item.get("financial_line_items_status") or "")
  archived=archived_pages(item)
  evidence_ok=bool(archived) and all(
   all(token in archived.get(page,"") for token in tokens)
   for page,tokens in spec["evidence"].items()
  )
  if not evidence_ok:
   print(f"TCX {period}: source-backed cash-flow repair skipped; exact B03a-CTCK tokens missing.")
   continue
  for field,value in spec["values"].items():
   record_value(
    item,field,value,
    "Source-backed correction from the archived VietstockFinance B03a-CTCK cash-flow statement; "
    f"{period}, PDF pages {','.join(map(str,spec['pages']))}. YTD reported values retained separately; standalone-quarter values are normalized from adjacent periods."
   )
  record_value(item,"cashflow_period_basis","year_to_date",
   "The archived B03a-CTCK reports cash flows cumulatively from 1 January.")
  if period=="2024-Q2":
   cash_beginning_calculation="Số dư đầu quý lấy từ số dư tiền cuối Q1/2024 theo B03a-CTCK."
  else:
   cash_beginning_calculation="Số dư tiền đầu năm lấy từ B03a-CTCK; không lấy số dư tiền ký quỹ của khách hàng."
  cash_ending_calculation="Số dư tiền và tương đương tiền cuối kỳ lấy trực tiếp từ B03a-CTCK."
  if item.get("cash_beginning_calculation")!=cash_beginning_calculation:
   item["cash_beginning_calculation"]=cash_beginning_calculation
   changed=True; field_count+=1
  if item.get("cash_ending_calculation")!=cash_ending_calculation:
   item["cash_ending_calculation"]=cash_ending_calculation
   changed=True; field_count+=1
  detail_fields_before=set(item.get("financial_line_items_extracted_fields") or [])
  detail_fields_after=detail_fields_before|set(spec["values"])|{"cashflow_period_basis"}
  if detail_fields_after!=detail_fields_before:
   item["financial_line_items_extracted_fields"]=sorted(detail_fields_after)
   changed=True; field_count+=1
  rejected_fields_before=set(item.get("financial_line_items_rejected_fields") or [])
  rejected_fields_after=rejected_fields_before-set(spec["values"])
  if rejected_fields_after!=rejected_fields_before:
   item["financial_line_items_rejected_fields"]=sorted(rejected_fields_after)
   changed=True; field_count+=1
  rejected_values=item.get("financial_line_items_rejected_values")
  if isinstance(rejected_values,dict):
   rejected_values_before=dict(rejected_values)
   for field in spec["values"]:
    rejected_values.pop(field,None)
   if rejected_values!=rejected_values_before:
    changed=True; field_count+=1
  flow_check={
   "source_policy":"VietstockFinance document catalog and linked PDF only",
   "source_index_url":item.get("source_index_url"),
   "source_document_url":item.get("source_url"),
   "source_archive_file":item.get("source_archive_file"),
   "report_form":"B03a-CTCK",
   "report_scope":"standalone securities-company report; not consolidated",
   "period":period,
   "pdf_pages":spec["pages"],
   "basis":"year_to_date_report_normalized_to_quarter",
   "exact_source_vnd":{field:int(round(value*1000000)) for field,value in spec["values"].items()},
   "source_tokens":{str(page):tokens for page,tokens in spec["evidence"].items()},
   "quarter_flows_sum_to_net_cash_change":round(sum(item.get(field,0) for field in ("operating_cash_flow","investing_cash_flow","financing_cash_flow"))-item.get("net_cash_change",0),6)==0,
   "ytd_flows_sum_to_net_cash_change":round(sum(item.get(field,0) for field in ("operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd"))-item.get("net_cash_change_ytd",0),6)==0,
   "opening_closing_cash_bridge_reconciles":round(item.get("cash_ending",0)-item.get("cash_beginning",0)-item.get("net_cash_change",0),6)==0,
   "visually_checked_rows":True,
   "note":"Số dư/luồng tiền thuộc công ty chứng khoán; không lấy dòng tiền môi giới/tiền ký quỹ của khách hàng. Q2 flows = Q2 YTD trừ Q1 YTD."
  }
  if item.get("cashflow_source_reconciliation")!=flow_check:
   item["cashflow_source_reconciliation"]=flow_check
   changed=True; field_count+=1
  note=(
   f"Đã đối chiếu trực quan B03a-CTCK VietstockFinance {period}, PDF trang "
   f"{','.join(map(str,spec['pages']))}: khôi phục lưu chuyển tiền kinh doanh/đầu tư/tài chính, biến động tiền thuần và số dư tiền của chính công ty; "
   "Q2 là chênh lệch số lũy kế giữa Q2 và Q1. Không dùng tiền ký quỹ của khách hàng."
  )
  old_note=str(item.get("financial_line_items_note") or "")
  if note not in old_note:
   item["financial_line_items_note"]=(old_note+" "+note).strip()
   changed=True; field_count+=1
  if field_count>cash24_start_field_count or cash24_start_status!="auto_extracted_pending_visual_review":
   item["financial_line_items_status"]="auto_extracted_pending_visual_review"
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True
   quarter_count+=1

 # TCX Q3/2024: repair detailed income, balance sheet, and cash-flow rows from
 # the visually checked stand-alone B01a/B02a/B03a documents linked by VietstockFinance.
 q3_2024=by_period.get("2024-Q3")
 if isinstance(q3_2024,dict):
  q3_pages=archived_pages(q3_2024)
  q3_income_evidence={
   9:[
    "486.643.912.660","24.982.287.730","706.030.635.948","126.282.007.934",
    "133.689.401.707","307.146.234.263","13.077.896.644","45.835.000.002",
    "140.001.708.018","57.988.277.358","11.422.180.299","48.790.239.246","981.043.051"
   ],
   10:["5.684.781.466","454.532.798.330","477.531.235.067","136.461.459.136","1.096.495.486.270","1.097.052.077.972"],
   11:["219.410.415.594","218.319.529.056","1.090.886.538","877.641.662.378"],
  }
  q3_income_ok=bool(q3_pages) and all(
   all(token in q3_pages.get(page,"") for token in tokens)
   for page,tokens in q3_income_evidence.items()
  )
  if q3_income_ok:
   q3_income_values={
    "revenue":1844805.107025,
    "broker_total_operating_revenue":1844805.107025,
    "broker_fvtpl_gain":486643.912660,
    "broker_held_to_maturity_income":24982.287730,
    "broker_lending_income":706030.635948,
    "broker_afs_income":126282.007934,
    "broker_brokerage_revenue":133689.401707,
    "broker_underwriting_revenue":307146.234263,
    "broker_custody_revenue":13077.896644,
    "broker_financial_advisory_revenue":45835.000002,
    "broker_other_operating_income":1117.730137,
    "broker_fvtpl_loss":20819.968064,
    "broker_total_operating_expenses":140001.708018,
    "broker_operating_expenses":140001.708018,
    "broker_brokerage_expense":57988.277358,
    "broker_custody_expense":11422.180299,
    "broker_other_operating_expense":48790.239246,
    "financial_income":5684.781466,
    "broker_financial_income":5684.781466,
    "financial_expense":477531.235067,
    "broker_financial_expense":477531.235067,
    "interest_expense":454532.798330,
    "broker_interest_expense":454532.798330,
    "admin_expense":136461.459136,
    "broker_admin_expenses":136461.459136,
    "operating_profit":1096495.486270,
    "broker_net_operating_profit":1096495.486270,
    "income_tax":219410.415594,
    "income_tax_current":218319.529056,
    "income_tax_deferred":1090.886538,
   }
   q3_income_pages={
    field:(10 if field in {
     "financial_income","broker_financial_income","financial_expense","broker_financial_expense",
     "interest_expense","broker_interest_expense","admin_expense","broker_admin_expenses",
     "operating_profit","broker_net_operating_profit"
    } else (11 if field in {"income_tax","income_tax_current","income_tax_deferred"} else 9))
    for field in q3_income_values
   }
   q3_start_count=field_count
   q3_start_status=str(q3_2024.get("financial_line_items_status") or "")
   for field,value in q3_income_values.items():
    record_value(
     q3_2024,field,value,
     f"Visually checked in the archived VietstockFinance B02a-CTCK Q3/2024 statement, PDF page {q3_income_pages[field]}; current-quarter column; source VND divided by 1,000,000."
    )
   q3_fields_before=set(q3_2024.get("financial_line_items_extracted_fields") or [])
   q3_fields_after=q3_fields_before|set(q3_income_values)
   if q3_fields_after!=q3_fields_before:
    q3_2024["financial_line_items_extracted_fields"]=sorted(q3_fields_after)
    changed=True; field_count+=1
   q3_rejected_before=set(q3_2024.get("financial_line_items_rejected_fields") or [])
   q3_rejected_after=q3_rejected_before-set(q3_income_values)
   if q3_rejected_after!=q3_rejected_before:
    q3_2024["financial_line_items_rejected_fields"]=sorted(q3_rejected_after)
    changed=True; field_count+=1
   q3_rejected_values=q3_2024.get("financial_line_items_rejected_values")
   if isinstance(q3_rejected_values,dict):
    rejected_values_before=dict(q3_rejected_values)
    for field in q3_income_values:
     q3_rejected_values.pop(field,None)
    if rejected_values!=rejected_values_before:
     changed=True; field_count+=1
   q3_income_meta={
    "source_policy":"VietstockFinance document catalog and linked PDF only",
    "source_index_url":q3_2024.get("source_index_url"),
    "source_document_url":q3_2024.get("source_url"),
    "source_archive_file":q3_2024.get("source_archive_file"),
    "report_form":"B02a-CTCK",
    "report_scope":"standalone securities-company report; not consolidated",
    "pdf_pages":[9,10,11],
    "manually_visual_reviewed":True,
    "exact_source_vnd":{field:int(round(value*1000000)) for field,value in q3_income_values.items()},
    "source_tokens":{str(page):tokens for page,tokens in q3_income_evidence.items()},
    "derived_residual_fields":{"broker_other_operating_income":{"formula":"reported total operating revenue minus the other eight individually reported operating revenue rows","value_million_vnd":1117.730137,"source_page":9}},
    "note":"Revenue and expense rows are from the Quý 3 column on page 7; financial income/expense and operating profit from page 8; tax and after-tax profit from page 9. The other-operating-income amount is reconciled as the residual to reported total operating revenue after the other eight rows are matched. Combined row 24 is included only in total operating expenses, not relabelled as pure borrowing expense."
   }
   if q3_2024.get("financial_line_items_source_row_reconciliation")!=q3_income_meta:
    q3_2024["financial_line_items_source_row_reconciliation"]=q3_income_meta
    changed=True; field_count+=1
   pages_before=set(q3_2024.get("financial_line_items_source_pages") or [])
   pages_after=pages_before|{9,10,11}
   if pages_after!=pages_before:
    q3_2024["financial_line_items_source_pages"]=sorted(pages_after)
    changed=True; field_count+=1
   note="Đã đối chiếu trực quan B02a-CTCK VietstockFinance Q3/2024 trang 7–9: bổ sung tổng doanh thu hoạt động, các dòng thu nhập/chi phí, lợi nhuận hoạt động và thuế theo cột Quý 3; dòng chi phí tổng hợp số 24 không gán thành riêng chi phí lãi vay."
   old_note=str(q3_2024.get("financial_line_items_note") or "")
   if note not in old_note:
    q3_2024["financial_line_items_note"]=(old_note+" "+note).strip()
    changed=True; field_count+=1
   if field_count>q3_start_count or q3_start_status!="auto_extracted_pending_visual_review":
    q3_2024["financial_line_items_status"]="auto_extracted_pending_visual_review"
    q3_2024["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed=True; quarter_count+=1
  else:
   print("TCX 2024-Q3: income repair skipped because one or more source-token checks failed.")

 # Q3/2024 balance-sheet details from B01a-CTCK.
 q3_balance_values={
  "current_assets":46537938.169842,
  "non_current_assets":3330054.972010,
  "cash_and_equivalents":3265767.728843,
  "broker_held_to_maturity_assets":2031105.785348,
  "broker_lending_assets":25483299.379217,
  "broker_afs_assets":13495559.828376,
  "broker_receivables":457741.282392,
  "fixed_assets":47000.960029,
  "current_liabilities":20399876.486004,
  "long_term_liabilities":3878967.761208,
  "broker_short_term_borrowings":18250517.591201,
  "broker_short_term_bonds":750752.043752,
  "broker_long_term_bonds":3873429.871913,
  "retained_earnings":14184540.747501,
 }
 q3_balance_evidence={
  5:["46.537.938.169.842","2.031.105.785.348","25.483.299.379.217","457.741.282.392","3.330.054.972.010","47.000.960.029","49.867.993.141.852"],
  6:["24.278.844.247.212","20.399.876.486.004","3.878.967.761.208","18.250.517.591.201","750.752.043.752","3.873.429.871.913","14.184.540.747.501"],
 }
 if isinstance(q3_2024,dict):
  q3_balance_pages=archived_pages(q3_2024)
  q3_balance_ok=bool(q3_balance_pages) and all(
   all(token in q3_balance_pages.get(page,"") for token in tokens)
   for page,tokens in q3_balance_evidence.items()
  )
  if q3_balance_ok:
   q3_balance_start_count=field_count
   for field,value in q3_balance_values.items():
    record_value(
     q3_2024,field,value,
     f"Visually checked in the archived VietstockFinance B01a-CTCK Q3/2024 balance sheet, PDF page {5 if field in {'current_assets','non_current_assets','cash_and_equivalents','broker_held_to_maturity_assets','broker_lending_assets','broker_afs_assets','broker_receivables','fixed_assets'} else 6}; source VND divided by 1,000,000."
    )
   fields_before=set(q3_2024.get("financial_line_items_extracted_fields") or [])
   fields_after=fields_before|set(q3_balance_values)
   if fields_after!=fields_before:
    q3_2024["financial_line_items_extracted_fields"]=sorted(fields_after)
    changed=True; field_count+=1
   rejected_before=set(q3_2024.get("financial_line_items_rejected_fields") or [])
   rejected_after=rejected_before-set(q3_balance_values)
   if rejected_after!=rejected_before:
    q3_2024["financial_line_items_rejected_fields"]=sorted(rejected_after)
    changed=True; field_count+=1
   rejected_values=q3_2024.get("financial_line_items_rejected_values")
   if isinstance(rejected_values,dict):
    rejected_values_before=dict(rejected_values)
    for field in q3_balance_values:
     rejected_values.pop(field,None)
    if q3_rejected_values!=rejected_values_before:
     changed=True; field_count+=1
   q3_balance_meta={
    "source_policy":"VietstockFinance document catalog and linked PDF only",
    "source_index_url":q3_2024.get("source_index_url"),
    "source_document_url":q3_2024.get("source_url"),
    "source_archive_file":q3_2024.get("source_archive_file"),
    "report_form":"B01a-CTCK",
    "report_scope":"standalone securities-company report; not consolidated",
    "pdf_pages":[5,6],
    "manually_visual_reviewed":True,
    "fields":{field:{"value_million_vnd":value,"source_value_vnd":int(round(value*1000000))} for field,value in q3_balance_values.items()},
    "source_tokens":{str(page):tokens for page,tokens in q3_balance_evidence.items()},
   }
   if q3_2024.get("financial_line_items_balance_source_reconciliation")!=q3_balance_meta:
    q3_2024["financial_line_items_balance_source_reconciliation"]=q3_balance_meta
    changed=True; field_count+=1
   pages_before=set(q3_2024.get("financial_line_items_source_pages") or [])
   pages_after=pages_before|{5,6}
   if pages_after!=pages_before:
    q3_2024["financial_line_items_source_pages"]=sorted(pages_after)
    changed=True; field_count+=1
   note="Đã đối chiếu trực quan B01a-CTCK VietstockFinance Q3/2024 trang 3–4: bổ sung tiền, HTM, cho vay, AFS, phải thu, TSCĐ, tổng tài sản ngắn/dài hạn, nợ ngắn/dài hạn, vay/trái phiếu và lợi nhuận chưa phân phối."
   old_note=str(q3_2024.get("financial_line_items_note") or "")
   if note not in old_note:
    q3_2024["financial_line_items_note"]=(old_note+" "+note).strip()
    changed=True; field_count+=1
   if field_count>q3_balance_start_count:
    q3_2024["financial_line_items_status"]="auto_extracted_pending_visual_review"
    q3_2024["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed=True; quarter_count+=1
  else:
   print("TCX 2024-Q3: balance repair skipped because one or more source-token checks failed.")

 # Q3/2024 cash flow is shown cumulatively for nine months. Normalize to
 # standalone-quarter values by subtracting the Q2 YTD totals; opening cash is
 # the Q2 quarter close, not the year-start value printed on B03a-CTCK.
 q3_cash_values={
  "operating_cash_flow_ytd":-2321338.102096,
  "investing_cash_flow_ytd":-6046.969681,
  "financing_cash_flow_ytd":1010971.806432,
  "net_cash_change_ytd":-1316413.265345,
  "operating_cash_flow":3850747.500461,
  "investing_cash_flow":-43.490000,
  "financing_cash_flow":-3360409.560861,
  "net_cash_change":490294.449600,
  "capital_expenditure_ytd":-6046.969681,
  "capital_expenditure":-43.490000,
  "cash_beginning_reported_ytd":4582180.994188,
  "cash_beginning":2775473.279243,
  "cash_ending":3265767.728843,
  "cash_and_equivalents":3265767.728843,
 }
 q3_cash_evidence={
  12:["2.321.338.102.096","6.046.969.681"],
  13:["1.010.971.806.432","1.316.413.265.345","4.582.180.994.188","3.265.767.728.843"],
 }
 if isinstance(q3_2024,dict):
  q3_cash_pages=archived_pages(q3_2024)
  q3_cash_ok=bool(q3_cash_pages) and all(
   all(token in q3_cash_pages.get(page,"") for token in tokens)
   for page,tokens in q3_cash_evidence.items()
  )
  if q3_cash_ok:
   q3_cash_start_count=field_count
   for field,value in q3_cash_values.items():
    record_value(
     q3_2024,field,value,
     "Visually checked in the archived VietstockFinance B03a-CTCK Q3/2024 cash-flow statement, PDF pages 10–11. Q3 standalone flow is nine-month YTD less Q2 YTD; source VND divided by 1,000,000."
    )
   record_value(q3_2024,"cashflow_period_basis","year_to_date",
    "B03a-CTCK cash flows are reported cumulatively from 1 January.")
   cash_fields_before=set(q3_2024.get("financial_line_items_extracted_fields") or [])
   cash_fields_after=cash_fields_before|set(q3_cash_values)|{"cashflow_period_basis"}
   if cash_fields_after!=cash_fields_before:
    q3_2024["financial_line_items_extracted_fields"]=sorted(cash_fields_after)
    changed=True; field_count+=1
   rejected_before=set(q3_2024.get("financial_line_items_rejected_fields") or [])
   rejected_after=rejected_before-set(q3_cash_values)
   if rejected_after!=rejected_before:
    q3_2024["financial_line_items_rejected_fields"]=sorted(rejected_after)
    changed=True; field_count+=1
   rejected_values=q3_2024.get("financial_line_items_rejected_values")
   if isinstance(rejected_values,dict):
    rejected_values_before=dict(rejected_values)
    for field in q3_cash_values:
     rejected_values.pop(field,None)
    if rejected_values!=rejected_values_before:
     changed=True; field_count+=1
   q3_cash_meta={
    "source_policy":"VietstockFinance document catalog and linked PDF only",
    "source_index_url":q3_2024.get("source_index_url"),
    "source_document_url":q3_2024.get("source_url"),
    "source_archive_file":q3_2024.get("source_archive_file"),
    "report_form":"B03a-CTCK",
    "report_scope":"standalone securities-company report; not consolidated",
    "pdf_pages":[12,13],
    "basis":"nine_month_ytd_normalized_to_q3",
    "exact_source_vnd":{field:int(round(value*1000000)) for field,value in q3_cash_values.items()},
    "source_tokens":{str(page):tokens for page,tokens in q3_cash_evidence.items()},
    "quarter_flows_sum_to_net_cash_change":round(sum(q3_cash_values[field] for field in ("operating_cash_flow","investing_cash_flow","financing_cash_flow"))-q3_cash_values["net_cash_change"],6)==0,
    "ytd_flows_sum_to_net_cash_change":round(sum(q3_cash_values[field] for field in ("operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd"))-q3_cash_values["net_cash_change_ytd"],6)==0,
    "opening_closing_cash_bridge_reconciles":round(q3_cash_values["cash_ending"]-q3_cash_values["cash_beginning"]-q3_cash_values["net_cash_change"],6)==0,
    "visually_checked_rows":True,
    "note":"Số dư/luồng tiền thuộc công ty chứng khoán; không lấy dòng tiền môi giới/tiền ký quỹ của khách hàng. Q3 flows = 9-month YTD less Q2 YTD."
   }
   if q3_2024.get("cashflow_source_reconciliation")!=q3_cash_meta:
    q3_2024["cashflow_source_reconciliation"]=q3_cash_meta
    changed=True; field_count+=1
   for field,value in {
    "cash_beginning_calculation":"Số dư đầu Q3/2024 lấy từ số dư tiền cuối Q2/2024 theo B03a-CTCK.",
    "cash_ending_calculation":"Số dư tiền cuối Q3/2024 lấy trực tiếp từ B03a-CTCK.",
   }.items():
    if q3_2024.get(field)!=value:
     q3_2024[field]=value
     changed=True; field_count+=1
   note="Đã đối chiếu trực quan B03a-CTCK VietstockFinance Q3/2024 trang 10–11: dòng tiền quý III được tính bằng lũy kế 9 tháng trừ lũy kế 6 tháng; số dư đầu quý lấy theo số dư cuối Q2 và số dư cuối quý lấy trực tiếp từ báo cáo."
   old_note=str(q3_2024.get("financial_line_items_note") or "")
   if note not in old_note:
    q3_2024["financial_line_items_note"]=(old_note+" "+note).strip()
    changed=True; field_count+=1
   if field_count>q3_cash_start_count or q3_2024.get("financial_line_items_status")!="auto_extracted_pending_visual_review":
    q3_2024["financial_line_items_status"]="auto_extracted_pending_visual_review"
    q3_2024["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed=True; quarter_count+=1
  else:
   print("TCX 2024-Q3: cash-flow repair skipped because one or more source-token checks failed.")

 cash_specs={
  "2026-Q1":{
   "evidence":[
    (12,"5.364.921.379.297"),(13,"7.169.753.162.448"),
    (13,"2.385.094.712.445"),(13,"5.493.172.934.162")
   ],
   "operating_cash_flow_ytd":-5364921.379297,
   "financing_cash_flow_ytd":7169753.162448,
   "net_cash_change_ytd":2385094.712445,
   "cash_beginning_reported_ytd":3108078.221717,
   "cash_beginning":3108078.221717,
   "cash_ending":5493172.934162,
   "capital_expenditure_ytd":-19737.070706,
   "source_pages":[12,13],
  },
  "2026-Q2":{
   "evidence":[
    (12,"14.297.190.746.884"),(13,"178.884.893.621"),
    (13,"17.164.732.877.510"),(13,"3.046.427.024.247"),
    (13,"6.154.505.245.964")
   ],
   "operating_cash_flow_ytd":-14297190.746884,
   "investing_cash_flow_ytd":178884.893621,
   "financing_cash_flow_ytd":17164732.877510,
   "net_cash_change_ytd":3046427.024247,
   "cash_beginning_reported_ytd":3108078.221717,
   "cash_beginning":5493172.934162,
   "cash_ending":6154505.245964,
   "capital_expenditure_ytd":-35785.929930,
   "dividends_paid_ytd":-1155791.748000,
   "source_pages":[12,13],
  },
  "2026-Q3":{
   "evidence":[
    (12,"10.529.105.661.173"),(13,"141.487.840.021"),
    (13,"11.531.579.346.989"),(13,"1.143.961.525.837"),
    (13,"4.252.039.747.554")
   ],
   "operating_cash_flow_ytd":-10529105.661173,
   "investing_cash_flow_ytd":141487.840021,
   "financing_cash_flow_ytd":11531579.346989,
   "net_cash_change_ytd":1143961.525837,
   "cash_beginning_reported_ytd":3108078.221717,
   "cash_beginning":6154505.245964,
   "cash_ending":4252039.747554,
   "capital_expenditure_ytd":-38077.540900,
   "dividends_paid_ytd":-1155791.748000,
   "source_pages":[12,13],
  },
 }

 for period,spec in cash_specs.items():
  item=by_period.get(period)
  if not isinstance(item,dict):
   continue
  page_text=archived_pages(item)
  if not page_text or any(token not in page_text.get(page,"") for page,token in spec["evidence"]):
   print(f"TCX {period}: source-backed cashflow repair skipped; one or more exact report tokens were not found.")
   continue
  # The Q1 cash-flow page OCR misread the net-investing-flow row. Derive it
  # from the independently printed net cash change, operating flow and financing
  # flow, all of which reconcile to the reported opening/closing cash balances.
  corrected=dict(spec)
  if period=="2026-Q1":
   corrected["investing_cash_flow_ytd"]=round(
    corrected["net_cash_change_ytd"]
    -corrected["operating_cash_flow_ytd"]
    -corrected["financing_cash_flow_ytd"],6
   )
  corrected["cashflow_period_basis"]="year_to_date"
  for field,value in corrected.items():
   if field in {"evidence","source_pages"}:
    continue
   if field=="cashflow_period_basis":
    if item.get(field)!=value:
     item[field]=value; changed=True; field_count+=1
    continue
   reason=(
    "Source-backed correction from VietstockFinance CTCK cash-flow statement; "
    f"{period}, PDF pages {','.join(map(str,spec['source_pages']))}. "
    +(
     "Investing cash flow was derived from the reported net cash change minus the independently reported operating and financing flows because OCR misread the net-investing-flow row."
     if period=="2026-Q1" and field=="investing_cash_flow_ytd"
     else "YTD amount is kept separately; the standalone quarterly amount is computed as current YTD minus prior quarter YTD."
    )
   )
   record_value(item,field,value,reason)
  if period=="2026-Q1":
   record_value(item,"investing_cash_flow_ytd",corrected["investing_cash_flow_ytd"],
    "Derived from reported net cash change minus reported operating and financing cash flows; opening/closing cash bridge reconciles exactly.")
  record_value(item,"cash_and_equivalents",corrected["cash_ending"],
   "Exact closing cash and cash equivalents from VietstockFinance cash-flow statement (unit: million VND).")
  fields=set(item.get("financial_line_items_extracted_fields") or [])
  fields.update({
   "operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd",
   "net_cash_change_ytd","cashflow_period_basis","cash_beginning_reported_ytd",
   "cash_beginning","cash_ending","cash_and_equivalents","capital_expenditure_ytd"
  })
  if "dividends_paid_ytd" in corrected:
   fields.add("dividends_paid_ytd")
  item["financial_line_items_extracted_fields"]=sorted(fields)
  item["financial_line_items_rejected_fields"]=[
   field for field in (item.get("financial_line_items_rejected_fields") or [])
   if field not in {
    "operating_cash_flow","investing_cash_flow","financing_cash_flow",
    "net_cash_change","cash_beginning","cash_ending","cash_and_equivalents"
   }
  ]
  rejected_values=item.get("financial_line_items_rejected_values")
  if isinstance(rejected_values,dict):
   for field in (
    "operating_cash_flow","investing_cash_flow","financing_cash_flow",
    "net_cash_change","cash_beginning","cash_ending","cash_and_equivalents"
   ):
    rejected_values.pop(field,None)
  item.pop("financial_line_items_cash_check",None)
  item["cashflow_source_reconciliation"]={
   "source_policy":"VietstockFinance document catalog and linked PDF only",
   "scope":"standalone CTCK report (B03a-CTCK), not a consolidated report",
   "period":period,
   "source_archive_file":item.get("source_archive_file"),
   "source_index_url":item.get("source_index_url"),
   "source_document_url":item.get("source_url"),
   "source_pages":spec["source_pages"],
   "basis":"year_to_date_report_normalized_to_quarter",
   "ytd_components_sum_to_reported_net_cash_change":True,
   "opening_closing_cash_bridge_reconciles":True,
   "note":(
    "YTD cash flow is extracted from the original CTCK statement; quarterly values are derived from adjacent YTD periods. "
    "Q1 investing flow uses the independent net cash total and the two other reported flows because the OCR read the investing-flow row incorrectly."
   )
  }
  old_note=str(item.get("financial_line_items_note") or "")
  old_note=old_note.replace(
   "Dòng tiền tự trích xuất bị ẩn vì tổng các luồng tiền không khớp biến động tiền thuần.",""
  ).replace(
   "Số dư tiền đầu/cuối kỳ bị ẩn vì không khớp biến động tiền theo quý.",""
  ).strip()
  note=(
   f"Đã đối chiếu LCTT TCX {period} từ báo cáo riêng mẫu B03a-CTCK trên VietstockFinance. "
   "Dữ liệu gốc lũy kế được lưu riêng; số quý được tính bằng chênh lệch lũy kế và đã đối chiếu với biến động tiền/ số dư tiền."
  )
  if period=="2026-Q1":
   note+=" Dòng đầu tư quý I được suy ra từ biến động tiền thuần trừ dòng tiền kinh doanh và tài chính do OCR nhận nhầm dòng tổng đầu tư; công thức được lưu để truy vết."
  if note not in old_note:
   item["financial_line_items_note"]=(old_note+" "+note).strip()
   changed=True; field_count+=1
  item["financial_line_items_status"]="auto_extracted_pending_visual_review"
  item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
  changed=True
  quarter_count+=1

 # Recover missing headline income-statement values for Q1/Q2 2026 from
 # clearly labelled statement rows. Q1 was additionally checked against the
 # PDF page images; Q2 uses source text and exact subtotal arithmetic pending
 # visual review.
 income_specs={
  "2026-Q1":{
   "evidence":[
    (9,"2.783.203.426.368"),(9,"432.669.955.217"),
    (10,"10.790.870.005"),(10,"741.488.168.510"),
    (10,"688.724.696.403"),(10,"161.180.842.697"),
    (10,"1.458.655.329.949"),(11,"1.458.425.492.628"),
    (11,"310.792.063.136"),(11,"311.488.840.262"),
    (11,"696.777.126"),(11,"1.147.633.429.492"),(11,"497")
   ],
   "source_pages":[9,10,11],
   "values":{
    "revenue":2783203.426368,
    "broker_total_operating_revenue":2783203.426368,
    "broker_total_operating_expenses":432669.955217,
    "broker_operating_expenses":432669.955217,
    "broker_financial_income":10790.870005,
    "financial_income":10790.870005,
    "broker_financial_expense":741488.168510,
    "financial_expense":741488.168510,
    "broker_interest_expense":688724.696403,
    "interest_expense":688724.696403,
    "broker_admin_expenses":161180.842697,
    "admin_expense":161180.842697,
    "broker_net_operating_profit":1458655.329949,
    "operating_profit":1458655.329949,
    "pretax_profit":1458425.492628,
    "income_tax":310792.063136,
    "income_tax_current":311488.840262,
    "income_tax_deferred":-696.777126,
    "net_profit":1147633.429492,
    "eps":497
   }
  },
  "2026-Q2":{
   "evidence":[
    (10,"494.598.914.337"),(10,"10.177.834.027"),
    (10,"1.023.448.500.976"),(10,"888.967.633.276"),
    (10,"140.103.237.495"),(10,"2.096.645.870.954"),
    (11,"2.096.955.197.698"),(11,"405.061.593.230"),
    (11,"409.747.556.919"),(11,"4.685.963.689"),
    (11,"1.691.893.604.468"),(11,"610")
   ],
   "source_pages":[10,11],
   "values":{
    "broker_total_operating_expenses":494598.914337,
    "broker_operating_expenses":494598.914337,
    "broker_financial_income":10177.834027,
    "financial_income":10177.834027,
    "broker_financial_expense":1023448.500976,
    "financial_expense":1023448.500976,
    "broker_interest_expense":888967.633276,
    "interest_expense":888967.633276,
    "broker_admin_expenses":140103.237495,
    "admin_expense":140103.237495,
    "broker_net_operating_profit":2096645.870954,
    "operating_profit":2096645.870954,
    "revenue":3744618.689735,
    "broker_total_operating_revenue":3744618.689735,
    "pretax_profit":2096955.197698,
    "income_tax":405061.593230,
    "income_tax_current":409747.556919,
    "income_tax_deferred":-4685.963689,
    "net_profit":1691893.604468,
    "eps":610
   }
  }
 }
 for period,spec in income_specs.items():
  item=by_period.get(period)
  if not isinstance(item,dict):
   continue
  page_text=archived_pages(item)
  if not page_text or any(token not in page_text.get(page,"") for page,token in spec["evidence"]):
   print(f"TCX {period}: source-backed income repair skipped; a statement-row evidence token was not found.")
   continue
  for field,value in spec["values"].items():
   record_value(
    item,field,value,
    f"Re-read from the explicitly labelled CTCK income statement at VietstockFinance, PDF pages {','.join(map(str,spec['source_pages']))}. "
    +("Page-image visual cross-check for Q1; " if period=="2026-Q1" else "Source-text and statement-equation cross-check for Q2; ")
    +"monetary values converted from VND to million VND."
   )
  item["revenue_calculation"]=(
   "Q1 reported total operating revenue line 20 in B02a-CTCK, converted from VND to million VND."
   if period=="2026-Q1"
   else "Derived from the printed B02a-CTCK subtotal identity: operating result = operating revenue + financial income - operating expenses - financial expenses - administration expenses; source subtotals cross-checked."
  )
  fields=set(item.get("financial_line_items_extracted_fields") or [])
  fields.update(spec["values"].keys())
  item["financial_line_items_extracted_fields"]=sorted(fields)
  item["financial_line_items_status"]="auto_extracted_pending_visual_review" if period=="2026-Q2" else "source_text_reconciled_pending_visual_review"
  if period=="2026-Q1":
   manually=set(item.get("financial_line_items_manually_verified_fields") or [])
   manually.update(spec["values"].keys())
   item["financial_line_items_manually_verified_fields"]=sorted(manually)
  item["source_validation"]={
   **(item.get("source_validation") if isinstance(item.get("source_validation"),dict) else {}),
   "single_source_policy":"Chỉ danh mục VietstockFinance và tệp do danh mục đó liên kết.",
   "source_catalog_url":item.get("source_index_url"),
   "source_document_url":item.get("source_url"),
   "report_scope":"standalone",
   "scope_validation_required":False,
   "manual_review_blocking_automatic_extraction":False,
   "manually_visual_reviewed":period=="2026-Q1"
  }
  item["source_extract_review"]={
   **(item.get("source_extract_review") if isinstance(item.get("source_extract_review"),dict) else {}),
   "checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
   "source_index_url":item.get("source_index_url"),
   "source_report_url":item.get("source_url"),
   "manually_visual_reviewed":period=="2026-Q1",
   "method":"Source rows from archived VietstockFinance PDF; Q1 checked against the PDF page images; Q2 source-text/subtotal reconciliation pending visual review.",
   "source_pages":spec["source_pages"]
  }
  # These are standalone CTCK statements. The consolidated-only attribution
  # line must not be populated with a copy of total net profit.
  prior_attributable=item.get("net_profit_attributable")
  if isinstance(prior_attributable,(int,float)):
   item.setdefault("financial_line_items_prior_values",{}).setdefault("net_profit_attributable",prior_attributable)
   item.setdefault("financial_line_items_value_corrections",{})["net_profit_attributable"]={
    "previous_value":prior_attributable,"new_value":None,
    "reason":"Standalone CTCK statement does not report a parent-company-attributable profit line; do not duplicate total net profit into a consolidated-only metric."
   }
  item["net_profit_attributable"]=None
  item["financial_line_items_extracted_fields"]=[
   field for field in (item.get("financial_line_items_extracted_fields") or [])
   if field!="net_profit_attributable"
  ]
  item["core_financial_extracted_fields"]=[
   field for field in (item.get("core_financial_extracted_fields") or [])
   if field!="net_profit_attributable"
  ]
  item["financial_line_items_source"]=str(item.get("source_archive_file") or "")
  item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
  item["financial_line_items_note"]=(str(item.get("financial_line_items_note") or "")+
   f" Bổ sung/sửa các tổng doanh thu, chi phí tài chính, lợi nhuận và thuế TCX {period} theo dòng có nhãn trong BCTC riêng VietstockFinance; "+ 
   ("đã kiểm tra trực quan các trang 9–11 của PDF." if period=="2026-Q1" else "đã đối chiếu phép tính từ các tổng phụ, còn chờ kiểm tra trực quan PDF.")
  ).strip()
  changed=True
  quarter_count+=1
  field_count+=len(spec["values"])
 # Q3 is likewise a standalone CTCK report: remove any stale parent-company
 # attribution value carried forward by a generic parser.
 q3_attributable=by_period.get("2026-Q3")
 if isinstance(q3_attributable,dict):
  old_attributable=q3_attributable.get("net_profit_attributable")
  if isinstance(old_attributable,(int,float)):
   q3_attributable.setdefault("financial_line_items_prior_values",{}).setdefault("net_profit_attributable",old_attributable)
   q3_attributable.setdefault("financial_line_items_value_corrections",{})["net_profit_attributable"]={
    "previous_value":old_attributable,"new_value":None,
    "reason":"Standalone CTCK statement does not report a parent-company-attributable profit line; do not duplicate total net profit into a consolidated-only metric."
   }
  q3_attributable["net_profit_attributable"]=None
  q3_attributable["financial_line_items_extracted_fields"]=[
   field for field in (q3_attributable.get("financial_line_items_extracted_fields") or [])
   if field!="net_profit_attributable"
  ]

 # Q3/2026 source text is readable for the main CTCK statements, but the prior
 # parser confused an advisory-revenue row for total revenue and retained YTD
 # profit in quarter fields. Restore the values from the explicitly labelled
 # "Quý 3" columns, and label the report scope accurately as standalone.
 item=by_period.get("2026-Q3")
 if isinstance(item,dict):
  page_text=archived_pages(item)
  # Match the actual PDF page numbering: total operating expenses are on
  # continuation page 10, not page 9. OCR also reads the leading digit 5 as
  # a section symbol in long-term liabilities, so validate its numeric suffix.
  required={
   5:["B01a-CTCK","93.291.524.374.447","3.682.538.394.785","96.974.062.769.232"],
   6:["49.568.110.970.833","47.405.951.798.399","43.655.467.758.554","912.643.212.279"],
   9:["B02a-CTCK","3.534.194.399.247"],
   10:["2.152.639.191.936","1.159.965.383.620","201.046.195.357","249.734.488.798"],
   11:["2.152.263.245.328","1.747.895.861.879","404.367.383.449","525"],
  }
  source_ok=bool(page_text) and all(
   all(token in page_text.get(page,"") for token in tokens)
   for page,tokens in required.items()
  )
  if source_ok:
   q2=by_period.get("2026-Q2") or {}
   q3_values={
    "total_assets":96974062.769232,
    "total_liabilities":49568110.970833,
    "equity":47405951.798399,
    "current_assets":93291524.374447,
    "non_current_assets":3682538.394785,
    "current_liabilities":43655467.758554,
    "long_term_liabilities":5912643.212279,
    "fixed_assets":106887.587941,
    "cash_and_equivalents":4252039.747554,
    "broker_fvtpl_assets":117174.100300,
    "broker_held_to_maturity_assets":2148198.577180,
    "broker_lending_assets":54739637.688044,
    "broker_afs_assets":30254612.527109,
    "broker_receivables":1207088.802528,
    "broker_short_term_borrowings":40489276.680000,
    "broker_short_term_bonds":568291.779040,
    "broker_long_term_bonds":3000000.000000,
    "broker_customer_deposits":6224732.944496,
    "retained_earnings":5631677.282493,
    "revenue":3534194.399247,
    "broker_total_operating_revenue":3534194.399247,
    "broker_fvtpl_gain":724755.461396,
    "broker_held_to_maturity_income":30382.148346,
    "broker_lending_income":1561090.700500,
    "broker_afs_income":256160.789129,
    "broker_brokerage_revenue":199454.806412,
    "broker_underwriting_revenue":737039.362934,
    "broker_custody_revenue":20640.490118,
    "broker_financial_advisory_revenue":3332.999998,
    "broker_other_operating_income":1337.640414,
    "broker_total_operating_expenses":249734.488798,
    "broker_operating_expenses":249734.488798,
    "broker_fvtpl_loss":79578.325668,
    "broker_brokerage_expense":86730.362590,
    "broker_custody_expense":19210.886265,
    "broker_other_operating_expense":68560.143523,
    "broker_financial_income":229190.860464,
    "broker_financial_expense":1159965.383620,
    "broker_interest_expense":875504.605736,
    "broker_admin_expenses":201046.195357,
    "financial_income":229190.860464,
    "financial_expense":1159965.383620,
    "interest_expense":875504.605736,
    "admin_expense":201046.195357,
    "broker_net_operating_profit":2152639.191936,
    "operating_profit":2152639.191936,
    "pretax_profit":2152263.245328,
    "income_tax":404367.383449,
    "income_tax_current":431918.589958,
    "income_tax_deferred":-27551.206509,
    "net_profit":1747895.861879,
    "eps":525,
   }
   source_page_for_field={}
   for field,value in q3_values.items():
    source_page_for_field[field]=(
     5 if field in {"current_assets","non_current_assets","total_assets","cash_and_equivalents","fixed_assets",
                    "broker_fvtpl_assets","broker_held_to_maturity_assets","broker_lending_assets","broker_afs_assets",
                    "broker_receivables"}
     else 6 if field in {"total_liabilities","equity","current_liabilities","long_term_liabilities",
                         "retained_earnings","broker_short_term_borrowings","broker_short_term_bonds",
                         "broker_long_term_bonds","broker_customer_deposits"}
     else 9 if field in {"revenue","broker_total_operating_revenue","broker_fvtpl_gain",
                         "broker_held_to_maturity_income","broker_lending_income","broker_afs_income",
                         "broker_brokerage_revenue","broker_underwriting_revenue","broker_custody_revenue",
                         "broker_financial_advisory_revenue","broker_other_operating_income",
                         "broker_total_operating_expenses","broker_operating_expenses","broker_fvtpl_loss",
                         "broker_brokerage_expense","broker_custody_expense","broker_other_operating_expense"}
     else 10 if field in {"broker_financial_income","broker_financial_expense","broker_interest_expense",
                          "broker_admin_expenses","financial_income","financial_expense","interest_expense",
                          "admin_expense","broker_net_operating_profit","operating_profit"}
     else 11)
    record_value(
     item,field,value,
     f"Re-read from the separately reported Quý 3 column of the archived VietstockFinance CTCK statement, PDF page {source_page_for_field[field]}; not from the YTD column."
    )
   # Ratios use quarter profit and average balance sheet values, not nine-month profit.
   q2_assets=q2.get("total_assets")
   q2_equity=q2.get("equity")
   if not isinstance(q2_assets,(int,float)) or not isinstance(q2_equity,(int,float)):
    q2_assets=100592059.821282
    q2_equity=45782449.906020
   average_assets=(q2_assets+q3_values["total_assets"])/2
   average_equity=(q2_equity+q3_values["equity"])/2
   ratios={
    "average_total_assets":average_assets,
    "average_equity":average_equity,
    "roa":round(q3_values["net_profit"]/average_assets*400,2),
    "roe":round(q3_values["net_profit"]/average_equity*400,2),
   }
   for field,value in ratios.items():
    record_value(item,field,value,"Derived from the separately reported Q3 net profit and average opening/closing balance-sheet values; annualized quarter basis.")
   item["roa_formula"]="LNST quý III / bình quân tổng tài sản đầu và cuối quý × 4 × 100"
   item["roe_formula"]="LNST quý III / bình quân vốn chủ sở hữu đầu và cuối quý × 4 × 100"
   item["ratio_calculations"]={
    "roa":f"LNST riêng Q3/2026 {q3_values['net_profit']} triệu VND / bình quân tổng tài sản {average_assets} triệu VND × 4 × 100.",
    "roe":f"LNST riêng Q3/2026 {q3_values['net_profit']} triệu VND / bình quân vốn chủ sở hữu {average_equity} triệu VND × 4 × 100."
   }
   item["ratio_source_pages"]=[5,6,11]
   item["report_type"]="BCTC riêng TCX Q3/2026 (mẫu B01a-CTCK/B02a-CTCK; VietstockFinance; chưa soát xét)"
   validation=item.get("source_validation")
   if not isinstance(validation,dict):
    validation={}
   validation.update({
    "single_source_policy":"Chỉ danh mục VietstockFinance và tệp do danh mục đó liên kết.",
    "source_catalog_url":item.get("source_index_url"),
    "source_document_url":item.get("source_url"),
    "listing_title":item.get("source_archive_title") or "Báo cáo tài chính quý 3 năm 2026",
    "report_scope":"standalone",
    "scope_basis":"Lưu trữ PDF dùng mẫu B01a-CTCK/B02a-CTCK và tên công ty riêng; tiêu đề danh mục VietstockFinance không ghi Hợp nhất. Không gắn nhãn BCTC hợp nhất.",
    "scope_validation_required":False,
    "manual_review_blocking_automatic_extraction":False,
    "manually_visual_reviewed":False,
    "source_archive_file":item.get("source_archive_file"),
   })
   item["source_validation"]=validation
   item["core_financial_extracted_fields"]=sorted(set(item.get("core_financial_extracted_fields") or [])|{
    "total_assets","total_liabilities","equity","pretax_profit","net_profit"
   })
   item["core_financial_extraction_source"]=str(item.get("source_archive_file") or "")
   item["core_financial_extraction_pages"]=[5,6,9,10,11]
   item["core_financial_extraction_status"]="source_text_reconciled_pending_visual_review"
   item["verification_status"]="source_text_reconciled_pending_visual_review"
   item["core_financial_extraction_note"]=(
    "Các tổng tài sản, nợ phải trả và vốn chủ sở hữu được đọc từ BCTC riêng mẫu B01a-CTCK và khớp phương trình cân đối theo số VND gốc. "
    "Doanh thu hoạt động, lợi nhuận hoạt động, lợi nhuận trước thuế, LNST và EPS lấy từ cột riêng Quý 3 trên B02a-CTCK; không lấy tổng lũy kế 9 tháng. "
    "Đây là đối chiếu văn bản nguồn và phép tính, chưa xác nhận bằng kiểm tra trực quan toàn bộ trang PDF."
   )
   item["verification_status_note"]="BCTC riêng của CTCK TCX; dữ liệu nguồn chưa được gắn nhãn hợp nhất."
   item.pop("core_financial_extraction_manual_terminal",None)
   item.pop("core_financial_extraction_stable_evidence_count",None)
   item.pop("core_financial_extraction_stable_evidence_updated_at",None)
   item["core_financial_extraction_unverified_values_note"]=(
    "Giá trị lịch sử nằm riêng trong core_financial_extraction_unverified_values là giá trị của parser cũ; các số lợi nhuận của quý III từng lấy nhầm cột lũy kế 9 tháng. "
    "Các giá trị hiển thị hiện tại được đọc lại từ cột Quý 3 của báo cáo VietstockFinance."
   )
   item["financial_line_items_source"]=str(item.get("source_archive_file") or "")
   fields=set(item.get("financial_line_items_extracted_fields") or [])
   fields.update(q3_values.keys())
   fields.update({"cash_and_equivalents","current_assets","non_current_assets","current_liabilities","long_term_liabilities"})
   item["financial_line_items_extracted_fields"]=sorted(fields)
   rejected_fields=set(item.get("financial_line_items_rejected_fields") or [])
   rejected_fields.difference_update({"current_assets","non_current_assets","current_liabilities","cash_beginning","cash_ending"})
   item["financial_line_items_rejected_fields"]=sorted(rejected_fields)
   rejected_values=item.get("financial_line_items_rejected_values")
   if isinstance(rejected_values,dict):
    for field in ("current_assets","non_current_assets","current_liabilities","cash_beginning","cash_ending"):
     rejected_values.pop(field,None)
   item["financial_line_items_status"]="auto_extracted_pending_visual_review"
   item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   note=(
    "Bổ sung lại các trường trống TCX Q3/2026 từ cột Quý 3 và bảng cân đối BCTC riêng VietstockFinance; "
    "đã sửa doanh thu tổng bị nhầm thành doanh thu tư vấn 3.333 triệu và lợi nhuận bị nhầm cột lũy kế 9 tháng. "
    "Phạm vi báo cáo được ghi là BCTC riêng, không phải báo cáo hợp nhất. Giá/PE/PB không được suy ra từ báo cáo kế toán."
   )
   old_note=str(item.get("financial_line_items_note") or "")
   if note not in old_note:
    item["financial_line_items_note"]=(old_note+" "+note).strip()
   item["core_financial_extraction_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   item["quarter_profit_basis"]="quarter_column_reported"
   changed=True
   quarter_count+=1
   field_count+=len(q3_values)
  else:
   print("TCX 2026-Q3: statement-row repair skipped because archived VietstockFinance line-item evidence did not match.")
 return changed,quarter_count,field_count

def enrich_snapshot(path):
 snapshot=json.loads(path.read_text(encoding="utf-8"))
 symbol=str(snapshot.get("symbol") or path.stem.replace("financials-","")).upper()
 items=snapshot.get("items")
 if not isinstance(items,list): return False,0,0
 changed=False; quarter_count=0; field_count=0
 for item in items:
  if not isinstance(item,dict) or not period_key(item): continue
  report_type_text=str(item.get("report_type") or "")
  old_detail_schema=str(item.get("financial_line_items_schema_version") or "")
  detail_schema_migration=bool(item.get("financial_line_items_status") and old_detail_schema != DETAIL_SCHEMA_VERSION)
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

  # Do not mark the detail schema migrated until source pages are available;
  # otherwise an offline archive would suppress a later safe retry.
  if item.get("financial_line_items_status") and item.get("financial_line_items_schema_version") != DETAIL_SCHEMA_VERSION:
   item["financial_line_items_schema_version"]=DETAIL_SCHEMA_VERSION
   item["financial_line_items_schema_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True

  # A parser-version change invalidates only machine-extracted core values.
  # Preserve the old values for audit, clear them from visible metrics, and
  # re-extract against the already archived Vietstock PDF/ZIP pages. Manual
  # verification states are never cleared by this migration.
  old_parser_version=str(item.get("core_financial_extraction_parser_version") or "")
  core_review_statuses={"auto_pending_extraction","manual_review_required_pending_extraction","auto_extracted_pending_visual_review"}
  source_validation_for_parser=item.get("source_validation")
  if not isinstance(source_validation_for_parser,dict):
   source_validation_for_parser={}
  parser_migration_allowed=(
   item.get("verification_status") in core_review_statuses
   and source_validation_for_parser.get("automatic_extraction_exhausted") is not True
  )
  if old_parser_version!=CORE_EXTRACTION_PARSER_VERSION:
   if parser_migration_allowed:
    unverified=item.setdefault("core_financial_extraction_unverified_values",{})
    for field in ("total_assets","total_liabilities","equity","pretax_profit","net_profit","roa","roe"):
     previous_value=item.get(field)
     if isinstance(previous_value,(int,float)):
      unverified.setdefault(field,previous_value)
      item[field]=None
    if unverified:
     item["core_financial_extraction_unverified_values_parser_version"]=old_parser_version or "legacy-parser-before-ngan-vnd-unit-fix"
    item["core_financial_extracted_fields"]=[
     field for field in (item.get("core_financial_extracted_fields") or [])
     if field not in {"total_assets","total_liabilities","equity","pretax_profit","net_profit","roa","roe"}
    ]
    item["verification_status"]="auto_pending_extraction"
    item["core_financial_extraction_status"]="auto_pending_extraction"
    item["core_financial_extraction_note"]="Đang trích xuất lại chỉ tiêu lõi bằng bộ nhận diện đơn vị đã sửa; các giá trị OCR của bộ phân tích cũ được lưu riêng và không dùng để hiển thị."
    item["verification_status_note"]="Đang kiểm tra lại đơn vị Ngàn/Nghìn VND với PDF/ZIP gốc VietstockFinance."
    item.pop("core_financial_extraction_manual_terminal",None)
    item.pop("core_financial_extraction_stable_evidence_count",None)
    item.pop("core_financial_extraction_evidence_attempt_count",None)
    item.pop("core_financial_extraction_attempt_count",None)
    item.pop("core_financial_extraction_evidence_fingerprint",None)
    item.pop("core_financial_extraction_calculations",None)
    changed=True
    quarter_count+=1
   item["core_financial_extraction_parser_version"]=CORE_EXTRACTION_PARSER_VERSION
   changed=True

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
    "core_extraction_parser_version":CORE_EXTRACTION_PARSER_VERSION,
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
  core_pages_complete=core_extraction_pages_complete(item,symbol,pages,14)

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
   item.pop("core_financial_extraction_stable_evidence_count",None)
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
  elif not core_balance_ok and item.get("verification_status") in {"auto_pending_extraction","manual_review_required_pending_extraction"} and evidence_changed:
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
  elif (
   not core_balance_ok
   and item.get("verification_status") in {"auto_pending_extraction","manual_review_required_pending_extraction"}
   and not evidence_changed
   and previous_fingerprint
   and core_pages_complete
  ):
   # Do not retry forever when all target source pages are already archived and
   # the same page text still cannot produce a reconciled core snapshot. Two
   # unchanged evidence passes mark this quarter for manual visual review.
   stable_count=int(item.get("core_financial_extraction_stable_evidence_count") or 0)+1
   item["core_financial_extraction_stable_evidence_count"]=stable_count
   item["core_financial_extraction_stable_evidence_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
   changed=True
   field_count+=1
   if stable_count>=2:
    unverified={}
    for field in ("total_assets","total_liabilities","equity","pretax_profit","net_profit","roa","roe"):
     value=item.get(field)
     if isinstance(value,(int,float)):
      unverified[field]=value
      item[field]=None
    if unverified:
     item.setdefault("core_financial_extraction_unverified_values",{}).update(unverified)
    item["verification_status"]="manual_review_required_pending_extraction"
    item["core_financial_extraction_status"]="manual_review_required_pending_extraction"
    item["core_financial_extraction_manual_terminal"]=True
    item["core_financial_extraction_note"]="Đã có đủ trang nguồn mục tiêu nhưng hai lượt phân tích trên cùng văn bản vẫn không tạo được bộ chỉ tiêu lõi cân đối. Các số OCR chưa cân đối được lưu riêng để đối chiếu; chỉ tiêu chính chưa xác minh được để trống."
    item["verification_status_note"]="Cần đối chiếu trực quan với PDF VietstockFinance trước khi công bố các chỉ tiêu lõi."
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
   # Re-test previously rejected rows against source text when the parser schema changes.
   if not key.startswith("__") and key in suppressed and not detail_schema_migration:
    found.pop(key,None)
  if not found: continue
  found,rejected=sane_fields(item,found,symbol)
  # Clear old rejection flags only when the new parser re-identifies a numeric row
  # and the source scope is not explicitly blocked.
  if detail_schema_migration:
   scope_info=item.get("source_validation") if isinstance(item.get("source_validation"),dict) else {}
   if scope_info.get("scope_validation_required") is not True:
    old_rejections=set(item.get("financial_line_items_rejected_fields") or [])
    rejected_now=set(rejected)
    accepted_now={
     key for key,value in found.items()
     if not key.startswith("__") and isinstance(value,(int,float))
     and not isinstance(value,bool) and key not in rejected_now
    }
    recovered=old_rejections & accepted_now
    if recovered:
     item["financial_line_items_rejected_fields"]=sorted(old_rejections-recovered)
     rejection_values=item.setdefault("financial_line_items_rejected_values",{})
     prior_values=item.setdefault("financial_line_items_prior_values",{})
     for field in recovered:
      record=rejection_values.pop(field,None)
      if isinstance(record,dict) and isinstance(record.get("value"),(int,float)):
       prior_values.setdefault(field,record["value"])
     item["financial_line_items_rejected_recovered_fields"]=sorted(
      set(item.get("financial_line_items_rejected_recovered_fields") or [])|recovered
     )
     changed=True
     field_count+=len(recovered)
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
  # On a parser/schema migration, do not keep an old OCR number when the
  # corrected parser cannot confirm that field from the archived PDF. Blanks
  # are preferable to displaying a potentially mis-mapped figure.
  new_fields=[]
  cleared_fields=[]
  if detail_schema_migration:
   tracked_fields=set(item.get("financial_line_items_extracted_fields") or [])
   manually_verified=set(item.get("financial_line_items_manually_verified_fields") or [])
   for old_field in sorted(tracked_fields-manually_verified):
    if old_field.startswith("__") or old_field in found: continue
    old_value=item.get(old_field)
    if isinstance(old_value,(int,float)) and not isinstance(old_value,bool):
     item.setdefault("financial_line_items_prior_values",{}).setdefault(old_field,old_value)
     item.setdefault("financial_line_items_value_corrections",{})[old_field]={
      "previous_value":old_value,
      "new_value":None,
      "reason":"Withheld during parser migration because the corrected extraction could not confidently re-identify this line in the archived VietstockFinance report."
     }
     item[old_field]=None
     cleared_fields.append(old_field)
     changed=True
     field_count+=1
   if cleared_fields:
    item["financial_line_items_extracted_fields"]=sorted(tracked_fields-set(cleared_fields))
  if not found:
   if rejection_changed or cleared_fields: quarter_count+=1
   continue
  for field,value in found.items():
   if field.startswith("__"): continue
   if item.get(field) is None:
    item[field]=value; new_fields.append(field)
   elif (
    field in set(item.get("financial_line_items_manually_verified_fields") or [])
    and isinstance(item.get(field),(int,float))
    and not isinstance(item.get(field),bool)
   ):
    # Once a value has been explicitly verified against its source, automatic
    # OCR migrations may not replace it with a numerically plausible child row.
    pass
   elif (
    detail_schema_migration
    and field in set(item.get("financial_line_items_extracted_fields") or [])
    and field not in set(item.get("financial_line_items_manually_verified_fields") or [])
    and isinstance(item.get(field),(int,float))
    and not isinstance(item.get(field),bool)
    and isinstance(value,(int,float))
    and not isinstance(value,bool)
    and item.get(field)!=value
   ):
    previous_value=item[field]
    item.setdefault("financial_line_items_prior_values",{}).setdefault(field,previous_value)
    item.setdefault("financial_line_items_value_corrections",{})[field]={
     "previous_value":previous_value,
     "new_value":int(round(value)),
     "reason":"Re-extracted previously stored OCR field from the archived VietstockFinance report using corrected note-reference and first-period-dash handling."
    }
    item[field]=int(round(value))
    new_fields.append(field)
   elif (
    symbol in BANKS
    and field=="bank_dividend_and_capital_income"
    and field in set(item.get("financial_line_items_extracted_fields") or [])
    and isinstance(item.get(field),(int,float))
    and isinstance(item.get("revenue"),(int,float))
    and item.get(field)==item.get("revenue")
    and isinstance(value,(int,float))
    and value!=item.get(field)
   ):
    previous_value=item[field]
    item.setdefault("financial_line_items_prior_values",{}).setdefault(field,previous_value)
    item.setdefault("financial_line_items_value_corrections",{})[field]={
     "previous_value":previous_value,
     "new_value":int(round(value)),
     "reason":"Corrected a legacy extraction that duplicated total operating income into the separately labelled income-from-capital-contributions row; value reparsed from the archived VietstockFinance statement."
    }
    item[field]=int(round(value))
    new_fields.append(field)
   elif (
    symbol in BANKS
    and field in {"bank_customer_loans","bank_net_service_income","bank_investment_securities","bank_cash_on_hand","bank_deposits_and_loans_to_credit_institutions","bank_deposits_and_borrowings_from_credit_institutions","bank_interest_income","bank_interest_expense","bank_trading_securities_net","bank_other_operating_net","bank_dividend_and_capital_income","operating_cash_flow_ytd","investing_cash_flow_ytd","financing_cash_flow_ytd","capital_expenditure_ytd","dividends_paid_ytd","net_cash_change_ytd","cash_beginning","cash_ending"}
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
     "previous_value":old_value,"new_value":value,"reason":reasons.get(field,"Reparsed from the saved VietstockFinance row and reconciled to related statement subtotals.")
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
  if symbol in BANKS and isinstance(item.get("cash_and_equivalents"),(int,float)):
   opening=item.get("cash_beginning_reported_ytd",item.get("cash_beginning"))
   if item.get("cash_and_equivalents")==opening:
    previous=item["cash_and_equivalents"]
    item.setdefault("financial_line_items_prior_values",{}).setdefault("cash_and_equivalents",previous)
    item.setdefault("financial_line_items_value_corrections",{})["cash_and_equivalents"]={"previous_value":previous,"new_value":None,"reason":"Removed generic cash-and-equivalents value duplicated from B04 opening cash; bank cash is reported separately in B02."}
    item.pop("cash_and_equivalents",None)
    fields.discard("cash_and_equivalents")
    changed=True
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

 repair_changed,repair_quarters,repair_fields=repair_tcx_2026_source_rows(items,symbol)
 changed=changed or repair_changed
 quarter_count+=repair_quarters
 field_count+=repair_fields
 by_period={str(i.get("period")):i for i in items if isinstance(i,dict)}
 # Check total cash flow before turning cumulative YTD values into quarter values.
 # When every reported component exists and the mismatch is small, fix an OCR
 # row-selection error against the independently reported net cash-flow total.
 for item in items:
  if not isinstance(item,dict) or item.get("cashflow_period_basis")!="year_to_date":
   continue
  operating=item.get("operating_cash_flow_ytd")
  investing=item.get("investing_cash_flow_ytd")
  financing=item.get("financing_cash_flow_ytd")
  net=item.get("net_cash_change_ytd")
  if not all(isinstance(v,(int,float)) for v in (operating,investing,financing,net)):
   continue
  delta=int(round(net-(operating+investing+financing)))
  if delta and abs(delta)<=10000:
   previous=int(round(investing))
   corrected=previous+delta
   item.setdefault("financial_line_items_prior_values",{}).setdefault("investing_cash_flow_ytd",previous)
   item.setdefault("financial_line_items_value_corrections",{})["investing_cash_flow_ytd"]={
    "previous_value":previous,"new_value":corrected,
    "reason":"Corrected a small OCR row-selection error by reconciling the independently reported net cash flow to operating, investing and financing flows; fixed-asset purchases remain in capital_expenditure_ytd."
   }
   item["investing_cash_flow_ytd"]=corrected
   item["financial_line_items_extracted_fields"]=sorted(set(item.get("financial_line_items_extracted_fields") or [])|{"investing_cash_flow_ytd"})
   item.setdefault("source_extract_review",{})
   item["source_extract_review"].setdefault("cashflow_reconciliation",{})
   item["source_extract_review"]["cashflow_reconciliation"].update({
    "investing_cash_flow_ytd_before_reconciliation":previous,
    "investing_cash_flow_ytd_after_reconciliation":corrected,
    "net_cash_flow_control_delta_before_reconciliation":delta,
    "investment_flow_reconciled_to_independent_net_cash_flow":True
   })
   note="Dòng tiền đầu tư được đối chiếu với tổng lưu chuyển tiền thuần vì OCR bắt nhầm dòng mua sắm TSCĐ; giá trị trước sửa và lý do đã được lưu."
   item["financial_line_items_note"]=(str(item.get("financial_line_items_note") or "")+" "+note).strip()
   changed=True; field_count+=1
 for item in items:
  key=period_key(item) if isinstance(item,dict) else None
  if not key: continue
  year,quarter=key
  basis=item.get("cashflow_period_basis")
  tracked_fields=set(item.get("financial_line_items_extracted_fields") or [])
  rejected_fields=set(item.get("financial_line_items_rejected_fields") or [])
  manually_verified=set(item.get("financial_line_items_manually_verified_fields") or [])
  corrections=item.get("financial_line_items_value_corrections") or {}
  protected_fields=set(manually_verified)
  for field,correction in corrections.items():
   current_value=item.get(field)
   corrected_value=correction.get("new_value") if isinstance(correction,dict) else None
   if isinstance(current_value,(int,float)) and isinstance(corrected_value,(int,float)) and current_value==corrected_value and str(correction.get("reason") or "").strip():
    protected_fields.add(field)

  def track_quarter_field(field,formula):
   nonlocal changed,field_count
   if field in rejected_fields or field in protected_fields: return
   if not isinstance(item.get(field),(int,float)): return
   if field not in tracked_fields:
    tracked_fields.add(field)
    item["financial_line_items_extracted_fields"]=sorted(tracked_fields)
    item[field+"_calculation"]=formula
    if not item.get("financial_line_items_status"):
     item["financial_line_items_status"]="auto_extracted_pending_visual_review"
    item["financial_line_items_schema_version"]=DETAIL_SCHEMA_VERSION
    item["financial_line_items_schema_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    item["financial_line_items_source"]=str(item.get("source_archive_file") or "")
    item["financial_line_items_updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    old_note=str(item.get("financial_line_items_note") or "")
    formula_note="Lưu chuyển tiền quý được đối chiếu từ cột lũy kế báo cáo; công thức được ghi ở trường *_calculation và vẫn cần rà soát trực quan."
    if formula_note not in old_note:
     item["financial_line_items_note"]=(old_note+" "+formula_note).strip()
    changed=True; field_count+=1

  if basis=="year_to_date":
   for quarterly_field,ytd_field in CASHFLOW_QUARTER_FROM_YTD.items():
    if quarterly_field in rejected_fields or quarterly_field in protected_fields: continue
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
    track_quarter_field(quarterly_field,formula)
  elif basis=="quarterly_reported":
   for quarterly_field,ytd_field in CASHFLOW_QUARTER_FROM_YTD.items():
    if quarterly_field in rejected_fields or quarterly_field in protected_fields: continue
    current=item.get(ytd_field)
    if isinstance(current,(int,float)) and item.get(quarterly_field) is None:
     item[quarterly_field]=int(round(current))
     item[quarterly_field+"_calculation"]="reported as standalone quarter"
     changed=True; field_count+=1
    track_quarter_field(quarterly_field,"reported as standalone quarter")
  if basis=="year_to_date" and isinstance(item.get("cash_beginning"),(int,float)) and item.get("cash_beginning_reported_ytd") is None:
   item["cash_beginning_reported_ytd"]=item["cash_beginning"]
   changed=True; field_count+=1
  if quarter>1 and basis=="year_to_date":
   previous=by_period.get(f"{year}-Q{quarter-1}") or {}
   prev_cash=previous.get("cash_ending")
   if isinstance(prev_cash,(int,float)) and item.get("cash_beginning")!=prev_cash and "cash_beginning" not in protected_fields:
    item["cash_beginning"]=prev_cash
    item["cash_beginning_calculation"]="previous quarter closing cash"
    if "cash_beginning" not in rejected_fields and "cash_beginning" not in tracked_fields:
     tracked_fields.add("cash_beginning")
     item["financial_line_items_extracted_fields"]=sorted(tracked_fields)
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
  # Record processing time separately from fetchedAt (source-download time).
  # The browser can now choose the newest processed snapshot across origins.
  snapshot["processedAt"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
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
  # Do not report a successful run when enrichment failed. The previous
  # warning-only handler let the workflow mark an unprocessed ticker complete.
  import traceback
  traceback.print_exc()
  print(f"::error::{path.name}: {type(exc).__name__}: {exc}")
  raise
 return 0

if __name__=="__main__":
 raise SystemExit(main())
