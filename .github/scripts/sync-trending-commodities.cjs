const fs=require('node:fs');const path=require('node:path');
const SOURCE='https://www.thitruonghanghoa.com/';const OUTPUT=path.join('data','trending-commodities.json');
const watchlist=[
{slug:'gia-dau-tho-brent',name:'Dầu thô Brent',label:'BRENT CRUDE',category:'NĂNG LƯỢNG',unit:'USD/thùng'},
{slug:'gia-dau-tho-dubai',name:'Dầu thô Dubai',label:'DUBAI CRUDE OIL',category:'HÀNG HÓA',unit:'USD/thùng'},
{slug:'gia-khi-hoa-long-lng-nhat-ban',name:'LNG Nhật Bản',label:'LIQUEFIED NATURAL GAS, JAPAN',category:'NĂNG LƯỢNG',unit:'USD/MMBtu'},
{slug:'gia-khi-tu-nhien-my',name:'Khí tự nhiên US',label:'NATURAL GAS US',category:'NĂNG LƯỢNG',unit:'USD/MMBtu'},
{slug:'gia-cao-su-the-gioi',name:'Cao su',label:'RUBBER',category:'NÔNG SẢN',unit:'JPY/kg'},
{slug:'gia-cao-su-tsr20',name:'Cao su TSR20',label:'RUBBER, TSR20',category:'NÔNG SẢN',unit:'USD/tấn'},
{slug:'gia-nhom',name:'Nhôm',label:'ALUMINUM',category:'KIM LOẠI',unit:'USD/tấn'},
{slug:'gia-phan-ure',name:'Phân urê',label:'UREA',category:'PHÂN BÓN',unit:'USD/tấn'},
{slug:'gia-ca-phe-robusta',name:'Cà phê Robusta',label:'COFFEE ROBUSTA',category:'NÔNG SẢN',unit:'USD/tấn'},
{slug:'gia-thiec',name:'Thiếc',label:'TIN',category:'KIM LOẠI',unit:'USD/tấn'}];
const decode=s=>s.replace(/&nbsp;|&#160;/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;|&apos;/g,"'").replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
async function main(){const r=await fetch(SOURCE,{headers:{'user-agent':'Mozilla/5.0 (compatible; SoLieuMarketBot/1.0)'},signal:AbortSignal.timeout(25000)});if(!r.ok)throw Error('Nguồn trả HTTP '+r.status);const html=await r.text(),data=[];
for(const item of watchlist){const re=/<a\b([^>]*href=["']([^"']+)["'][^>]*)>([\s\S]*?)<\/a>/gi;let m;while((m=re.exec(html))){if(!m[2].includes(item.slug))continue;const t=decode(m[3]);const ps=[...t.matchAll(/([+−-]?\s*\d+(?:\.\d+)?)\s*%/g)];const ns=[...t.matchAll(/(?:^|\s)(\d[\d,]*(?:\.\d+)?)(?=\s|$)/g)].map(x=>Number(x[1].replace(/,/g,''))).filter(Number.isFinite);if(!ps.length||!ns.length)continue;const changePct=Number(ps.at(-1)[1].replace(/\s/g,'').replace('−','-')),price=ns.at(-1);if(!Number.isFinite(changePct)||!Number.isFinite(price)||price<=0)continue;data.push({...item,price,changePct,url:new URL(m[2],SOURCE).href,source:SOURCE});break;}}
if(data.length<3)throw Error('Chỉ trích xuất được '+data.length+' mặt hàng; không ghi đè snapshot cũ.');const out={source:SOURCE,fetchedAt:new Date().toISOString(),data:data.slice(0,10)};fs.mkdirSync(path.dirname(OUTPUT),{recursive:true});fs.writeFileSync(OUTPUT+'.tmp',JSON.stringify(out,null,2)+'\n');fs.renameSync(OUTPUT+'.tmp',OUTPUT);console.log('Đã cập nhật '+out.data.length+' mặt hàng từ '+SOURCE);out.data.forEach(x=>console.log(x.name+' | '+x.price+' | '+x.changePct+'%'));}
main().catch(e=>{console.error(e.message);process.exit(1);});