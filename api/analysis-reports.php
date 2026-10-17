<?php
declare(strict_types=1);
/* Isolated API. Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, REPORT_SYNC_TOKEN
   as Hostinger environment variables; never commit credentials. */
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
function out(int $status, array $data): never {
  http_response_code($status);
  echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}
function ev(string $key): string { $v=getenv($key); return $v===false?'':trim($v); }
function pdo_db(): PDO {
  foreach (['DB_HOST','DB_NAME','DB_USER'] as $k) if (ev($k)==='') throw new RuntimeException('DB not configured');
  return new PDO('mysql:host='.ev('DB_HOST').';dbname='.ev('DB_NAME').';charset=utf8mb4',ev('DB_USER'),ev('DB_PASSWORD'),[
    PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC,PDO::ATTR_EMULATE_PREPARES=>false
  ]);
}
function safe_date($v): ?string {
  if (!is_string($v)||!preg_match('/^20\d{2}-\d{2}-\d{2}$/',$v)) return null;
  $d=DateTime::createFromFormat('!Y-m-d',$v); return $d&&$d->format('Y-m-d')===$v?$v:null;
}
function source_ok(string $url): bool {
  $h=strtolower((string)parse_url($url,PHP_URL_HOST));
  foreach (['vietstock.vn','cafef.vn','vietcap.com.vn','shs.com.vn','dsc.com.vn','bsc.com.vn','acbs.com.vn','mbs.com.vn','fpts.com.vn','hsc.com.vn','vndirect.com.vn','ssi.com.vn','kbsec.com.vn','yuanta.com.vn','masvn.com','vcbs.com.vn'] as $d)
    if ($h===$d||str_ends_with($h,'.'.$d)) return true;
  return false;
}
try {
  $method=$_SERVER['REQUEST_METHOD']??'GET';
  if ($method==='POST') {
    $token=ev('REPORT_SYNC_TOKEN'); $sent=(string)($_SERVER['HTTP_X_REPORT_SYNC_TOKEN']??'');
    if ($token===''||!hash_equals($token,$sent)) out(401,['ok'=>false,'error'=>'Unauthorized']);
    $raw=file_get_contents('php://input');
    if ($raw===false||strlen($raw)>5000000) out(413,['ok'=>false,'error'=>'Payload too large']);
    $payload=json_decode($raw,true,64,JSON_THROW_ON_ERROR);
    if (!is_array($payload)||!isset($payload['reports'])||!is_array($payload['reports'])) out(400,['ok'=>false,'error'=>'Invalid payload']);
    $db=pdo_db(); $db->beginTransaction();
    $up=$db->prepare("INSERT INTO analysis_reports (id,symbol,title,publisher,report_date,category,source_name,source_url,access_type,pdf_pages,pdf_bytes,pdf_status,summary,summary_status,extracted_at)
      VALUES (:id,:symbol,:title,:publisher,:rdate,:category,:source,:url,'public_link',:pages,:bytes,:pstatus,:summary,:sstatus,:extracted)
      ON DUPLICATE KEY UPDATE symbol=VALUES(symbol),title=VALUES(title),publisher=VALUES(publisher),report_date=VALUES(report_date),category=VALUES(category),source_name=VALUES(source_name),source_url=VALUES(source_url),pdf_pages=VALUES(pdf_pages),pdf_bytes=VALUES(pdf_bytes),pdf_status=VALUES(pdf_status),summary=VALUES(summary),summary_status=VALUES(summary_status),extracted_at=VALUES(extracted_at)");
    $mi=$db->prepare("INSERT IGNORE INTO analysis_report_metrics (report_id,metric_name,metric_value,unit,period_label,source_excerpt,review_status) VALUES (:id,:name,:value,:unit,:period,:excerpt,'needs_review')");
    $saved=0;$metrics=0;
    foreach($payload['reports'] as $r) {
      if(!is_array($r)) continue;
      $id=substr((string)($r['id']??''),0,190);$title=trim((string)($r['title']??''));$url=trim((string)($r['source_url']??''));
      if($id===''||$title===''||!filter_var($url,FILTER_VALIDATE_URL)||!in_array(parse_url($url,PHP_URL_SCHEME),['http','https'],true)||!source_ok($url)) continue;
      $sym=strtoupper((string)($r['symbol']??''));if($sym!==''&&!preg_match('/^[A-Z0-9]{1,16}$/',$sym))$sym='';
      $summary=mb_substr(trim((string)($r['summary']??'')),0,1600);
      $up->execute([':id'=>$id,':symbol'=>$sym?:null,':title'=>mb_substr($title,0,500),':publisher'=>mb_substr((string)($r['publisher']??''),0,190)?:null,':rdate'=>safe_date($r['report_date']??null),':category'=>preg_match('/^[a-z_]{3,80}$/',(string)($r['category']??''))?$r['category']:'brokerage_research',':source'=>mb_substr((string)($r['source_name']??'Vietstock eDocuments'),0,120),':url'=>$url,':pages'=>isset($r['pdf_pages'])?max(0,(int)$r['pdf_pages']):null,':bytes'=>isset($r['pdf_bytes'])?max(0,(int)$r['pdf_bytes']):null,':pstatus'=>in_array(($r['pdf_status']??''),['valid_pdf','link_only','unavailable','not_pdf'],true)?$r['pdf_status']:'link_only',':summary'=>$summary?:null,':sstatus'=>in_array(($r['summary_status']??''),['extractive','pending','needs_review'],true)?$r['summary_status']:'pending',':extracted'=>isset($r['extracted_at'])?date('Y-m-d H:i:s',strtotime((string)$r['extracted_at'])):null]);
      $saved++;
      foreach(($r['metrics']??[]) as $m) {
        if(!is_array($m)||!isset($m['name'],$m['value'])||!is_numeric($m['value']))continue;
        $mi->execute([':id'=>$id,':name'=>mb_substr((string)$m['name'],0,120),':value'=>$m['value'],':unit'=>mb_substr((string)($m['unit']??''),0,60)?:null,':period'=>mb_substr((string)($m['period']??''),0,80)?:null,':excerpt'=>mb_substr((string)($m['excerpt']??''),0,500)?:null]);$metrics+=$mi->rowCount();
      }
    }
    $db->commit();out(200,['ok'=>true,'received'=>count($payload['reports']),'saved'=>$saved,'new_metric_candidates'=>$metrics,'updated_at'=>gmdate('c')]);
  }
  if($method!=='GET'){header('Allow: GET, POST');out(405,['ok'=>false,'error'=>'Method not allowed']);}
  $db=pdo_db();$limit=max(1,min(100,(int)($_GET['limit']??50)));$sym=strtoupper(trim((string)($_GET['symbol']??'')));
  $where='';$params=[];if($sym!==''){$where='WHERE symbol=:symbol';$params[':symbol']=$sym;}
  $q=$db->prepare("SELECT id,symbol,title,publisher,report_date,category,source_name,source_url,access_type,pdf_pages,pdf_bytes,pdf_status,summary,summary_status,extracted_at,updated_at FROM analysis_reports $where ORDER BY report_date DESC,title ASC LIMIT $limit");
  $q->execute($params);$rows=$q->fetchAll();$mq=$db->prepare("SELECT metric_name AS name,metric_value AS value,unit,period_label AS period,source_excerpt AS excerpt,review_status FROM analysis_report_metrics WHERE report_id=:id ORDER BY metric_name");
  foreach($rows as &$row){$mq->execute([':id'=>$row['id']]);$row['metrics']=$mq->fetchAll();}unset($row);
  out(200,['ok'=>true,'updated_at'=>gmdate('c'),'reports'=>$rows]);
} catch(Throwable $e) {
  if(isset($db)&&$db instanceof PDO&&$db->inTransaction())$db->rollBack();
  error_log('[analysis-reports-api] '.$e->getMessage());
  out(503,['ok'=>false,'error'=>'Report database is unavailable or not configured']);
}
