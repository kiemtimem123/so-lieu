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
  print(f"::warning::{path.name}: {exc}")
 return 0

if __name__=="__main__":
 raise SystemExit(main())
