#!/usr/bin/env python3
"""Prepare a compact, rights-aware payload for the website DB API.

PDF bytes are streamed into memory only; no PDF or full extracted text is persisted.
Automatically extracted numeric candidates remain unreviewed and must not be treated
as verified financial facts.
"""
from __future__ import annotations
import hashlib, io, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/'data'/'analysis-reports.json'
OUT=ROOT/'reports'/'analysis'/'db-sync-payload.json'
NOW=datetime.now(timezone.utc).isoformat()
MAX_PDF_BYTES=int(os.getenv('MAX_PDF_BYTES','12000000'))
TIMEOUT=int(os.getenv('PDF_TIMEOUT_SECONDS','35'))
HEADERS={'User-Agent':'solieutaichinh-report-metadata-sync/1.0 (public research index)','Accept':'application/pdf,*/*;q=0.8'}
ALLOWED={'finance.vietstock.vn','edocs.vietstock.vn','static1.vietstock.vn','vietstock.vn','www.vietstock.vn','cafef.vn','www.cafef.vn','vietcap.com.vn','www.vietcap.com.vn','shs.com.vn','www.shs.com.vn','dsc.com.vn','www.dsc.com.vn','bsc.com.vn','new.bsc.com.vn','acbs.com.vn','mbs.com.vn','fpts.com.vn','hsc.com.vn','vndirect.com.vn','ssi.com.vn','kbsec.com.vn','yuanta.com.vn','masvn.com','vcbs.com.vn'}
FINANCE_TERMS=('doanh thu','lợi nhuận','tài sản','vốn chủ','nợ phải trả','eps','roe','roa','p/e','p/b','giá mục tiêu','khuyến nghị','tăng trưởng','biên lợi nhuận','dự phóng','định giá','ebitda','cash flow','revenue','net profit')
METRIC_PATTERNS=[
 ('EPS',r'\bEPS\b[^\d\n]{0,30}([-+]?\d[\d.,]*)'),
 ('ROE',r'\bROE\b[^\d\n]{0,20}([-+]?\d[\d.,]*)\s*%?'),
 ('ROA',r'\bROA\b[^\d\n]{0,20}([-+]?\d[\d.,]*)\s*%?'),
 ('P/E',r'\bP\s*/\s*E\b[^\d\n]{0,20}([-+]?\d[\d.,]*)'),
 ('P/B',r'\bP\s*/\s*B\b[^\d\n]{0,20}([-+]?\d[\d.,]*)'),
 ('Giá mục tiêu',r'(?:giá mục tiêu|target price)[^\d\n]{0,35}([-+]?\d[\d.,]*)'),
]
def host_ok(url):
 h=(urlparse(url).hostname or '').lower()
 return urlparse(url).scheme=='https' and any(h==d or h.endswith('.'+d) for d in ALLOWED)
def safe_get(session, url):
 for _ in range(6):
  if not host_ok(url): raise ValueError('URL or redirect host is not allowlisted HTTPS')
  response=session.get(url,timeout=TIMEOUT,stream=True,allow_redirects=False)
  if response.status_code in (301,302,303,307,308):
   location=response.headers.get('Location','')
   response.close()
   if not location: raise ValueError('Redirect missing Location')
   url=urljoin(url,location)
   continue
  return response
 raise ValueError('Too many redirects')
def compact(text):
 text=re.sub(r'\s+',' ',text or '').strip()
 return text
def summarize(text):
 paragraphs=[compact(p) for p in re.split(r'[\r\n]+',text or '')]
 paragraphs=[p for p in paragraphs if 70<=len(p)<=500]
 scored=[]
 for p in paragraphs:
  low=p.lower(); score=sum(1 for term in FINANCE_TERMS if term in low)
  if score: scored.append((score,p))
 chosen=[]
 for _,p in sorted(scored,key=lambda x:(-x[0],len(x[1]))):
  if all(p not in old and old not in p for old in chosen): chosen.append(p)
  if len(chosen)>=3: break
 summary=' '.join(chosen)
 return summary[:1500] if summary else ''
def extract_metrics(text):
 out=[]
 for name,pattern in METRIC_PATTERNS:
  for m in re.finditer(pattern,text or '',re.I):
   raw=m.group(1)
   # Avoid guessing locale for values with both separators; retain a candidate only if unambiguous.
   val=raw.replace(' ','')
   if ',' in val and '.' in val: continue
   if val.count(',')>1 or val.count('.')>1: continue
   val=val.replace(',','.')
   try: number=float(val)
   except ValueError: continue
   start=max(0,m.start()-70);end=min(len(text),m.end()+90)
   excerpt=compact((text or '')[start:end])[:450]
   out.append({'name':name,'value':number,'unit':'%' if name in ('ROE','ROA') else None,'period':None,'excerpt':excerpt})
   break
 return out
def main():
 if not CATALOG.exists(): raise SystemExit('Missing data/analysis-reports.json')
 catalog=json.loads(CATALOG.read_text(encoding='utf-8'))
 reports=[];session=requests.Session();session.headers.update(HEADERS)
 for item in catalog.get('reports',[]):
  url=str(item.get('downloadUrl') or item.get('url') or item.get('landingUrl') or '')
  if not url or not host_ok(url): continue
  row={'id':'research-'+hashlib.sha256(url.encode('utf-8')).hexdigest()[:40],'symbol':item.get('symbol'),'title':item.get('title') or 'Báo cáo phân tích','publisher':item.get('publisher'),'report_date':item.get('reportDate'),'category':item.get('category') or 'brokerage_research','source_name':item.get('source') or 'Nguồn công khai','source_url':url,'pdf_status':'link_only','summary':'','summary_status':'pending','metrics':[],'extracted_at':NOW}
  try:
   with safe_get(session,url) as res:
    res.raise_for_status()
    ctype=(res.headers.get('Content-Type') or '').lower()
    buf=bytearray()
    for chunk in res.iter_content(65536):
     if not chunk: continue
     buf.extend(chunk)
     if len(buf)>MAX_PDF_BYTES: raise ValueError('PDF exceeds configured size cap')
    if not (bytes(buf[:5])==b'%PDF-' or 'application/pdf' in ctype):
     row['pdf_status']='not_pdf'
    else:
     reader=PdfReader(io.BytesIO(bytes(buf)),strict=False)
     if reader.is_encrypted: raise ValueError('encrypted PDF')
     row['pdf_pages']=len(reader.pages);row['pdf_bytes']=len(buf);row['pdf_status']='valid_pdf'
     # Only extract text in memory. Persist a short extractive summary and limited metric candidates.
     text='\n'.join((p.extract_text() or '') for p in reader.pages[:20])
     summary=summarize(text)
     if summary:
      row['summary']=summary;row['summary_status']='needs_review'
     row['metrics']=extract_metrics(text)[:8]
  except Exception as e:
   print(json.dumps({'event':'report_pdf_skipped','id':row['id'],'reason':str(e)[:180]},ensure_ascii=False),file=sys.stderr)
  reports.append(row)
 payload={'schemaVersion':1,'generatedAt':NOW,'policy':{'pdf_archived':False,'full_text_persisted':False,'metric_candidates_default_status':'needs_review'},'reports':reports}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'reports':len(reports),'valid_pdfs':sum(r['pdf_status']=='valid_pdf' for r in reports),'summaries':sum(bool(r['summary']) for r in reports),'metric_candidates':sum(len(r['metrics']) for r in reports),'output':str(OUT.relative_to(ROOT))},ensure_ascii=False))
if __name__=='__main__': main()
