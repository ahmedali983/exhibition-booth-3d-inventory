from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests,json,re,time,base64,subprocess,collections,random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
ROOT=Path(__file__).resolve().parent
API='https://api.sketchfab.com/v3/search'
BASE='ahmedali983/exhibition-booth-3d-inventory'
REF='feature/expovault-bulk-range-prosceneverse'
terms=['exhibition stand','exhibition booth','trade show booth','trade show stand',
       'expo stand','expo booth','exhibition stall','exhibition booth design','trade fair booth','exhibit booth']
prior=json.loads((ROOT/'worldwide_licensed_booth_candidates_20261106.json').read_text(encoding='utf-8'))
old=set(x['uid'] for x in prior['items'])
# include all Wave12/13/14 source IDs now recorded on Github
cmd=['gh','api','--method','GET',f'repos/{BASE}/contents/catalog/expovault_known_uids_232_20261106.json','-f',f'ref={REF}']
r=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
if r.returncode==0:
 j=json.loads(r.stdout)
 try: old.update(json.loads(base64.b64decode(j['content']))['uids'])
 except Exception as e:print('UNABLE_TO_PARSE_BASELINE',str(e)[:100])
else:
 old.update(['ef43f32b29854d07b6ec7f69a32a7b03','85fb569c76aa40a39d9b6aba4203cfca','d6ae2a35cc554a89908548b3ff6a529c','55b8067ea0314b978358bd285b03e4b5'])
 print('BASELINE_FALLBACK',r.stderr[:90])
banned=re.compile(r'photo.?booth|dj.?booth|phone.?booth|voting.?booth|minecraft|roblox|vrchat|game.*booth|casin|toilet|bus station|kiosk screen|flag stand|speaker|chair|furniture|amusement|advertising banner|sign stand|lighting stand|statue|portrait|exhibition painting|sculpture|model plane|car stand',re.I)
relevant=re.compile(r'exhibition|expo|trade.?show|trade.?fair|tradeshow|convention|booth|stall|pavilion|stand|exhibit',re.I)
def ses():
 s=requests.Session()
 s.headers['User-Agent']='ExpoVault-rights-first-author-approved-public-catalog/3.0'
 s.mount('https://',HTTPAdapter(max_retries=Retry(total=2,backoff_factor=0.9,status_forcelist=(429,500,502,503,504),respect_retry_after_header=True)))
 return s
def crawl(term):
 s=ses();u=API;p={'type':'models','q':term,'downloadable':'true','count':24}
 arr=[];errors=[];visited=0
 for j in range(28):
  if not u:break
  try:
   r=s.get(u,params=p,timeout=(10,25));r.raise_for_status()
   data=r.json();page=data.get('results') or []
   arr.extend(page);u=data.get('next');p=None;visited+=1
   if not page:break
   time.sleep(.22)
  except Exception as e:
   errors.append(str(e)[:160]);break
 print('QUERY',repr(term),'PAGES',visited,'RESULTS',len(arr),'MORE',bool(u),'ERRORS',len(errors),flush=True)
 return term,arr,errors
records={};errors=[];stats=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 tasks={pool.submit(crawl,t):t for t in terms}
 for f in as_completed(tasks):
  term,entries,err=f.result(); errors.extend([{'term':term,'error':e} for e in err])
  stats.append({'term':term,'entries':len(entries),'errors':len(err)})
  for e in entries:
   uid=str(e.get('uid') or '')
   title=str(e.get('name') or '')
   if not re.fullmatch('[0-9a-f]{32}',uid) or uid in old or banned.search(title):continue
   if not e.get('isDownloadable') or e.get('isAgeRestricted'):continue
   lic=str((e.get('license') or {}).get('label') or '').lower()
   if 'noncommercial' in lic or 'no derivatives' in lic:continue
   if not any(v in lic for v in ['attribution','cc0','public domain']):continue
   tags=[x.get('name','') for x in e.get('tags') or [] if isinstance(x,dict)]
   desc=re.sub('<[^>]+>',' ',str(e.get('description') or ''))[:850]
   if not relevant.search(title+' '+desc+' '+' '.join(tags)):continue
   score=0
   if re.search('exhibition.*(booth|stand|stall)|trade.?show.*(booth|stand)|expo.*(booth|stand)|booth.*design',title,re.I):score+=80
   if re.search('exhibition|expo|trade.?show|trade.?fair|event',title,re.I):score+=40
   if re.search('booth|stand|stall|pavilion',title,re.I):score+=20
   faces=int(e.get('faceCount') or 0)
   if 10000 <= faces <= 5000000: score+=12
   score+=min(25,int(e.get('likeCount') or 0)//4)
   creator=(e.get('user') or {}).get('username') or ''
   row=records.setdefault(uid,{'uid':uid,'title':title,'description':desc,'tags':tags,'creator':creator,'source_url':e.get('viewerUrl') or 'https://sketchfab.com/models/'+uid,'license_label':lic,'face_count':faces,'likes':int(e.get('likeCount') or 0),'views':int(e.get('viewCount') or 0),'score':score,'terms':[]})
   if term not in row['terms']:row['terms'].append(term)
rows=sorted(records.values(),key=lambda x:(-x['score'],-x['likes'],-x['face_count']))
out={'run_date':'2026-11-06','source':'Official Sketchfab public API, 28 pages max per query; metadata only','old_excluded_count':len(old),'new_discovered_count':len(rows),'strong_title_count':sum(x['score']>=125 for x in rows),'terms':stats,'errors':errors,'results':rows,'warning':'No downloaded files, live permissions or 3D full-stand acceptance inferred; check original author rights before archiving.'}
target=ROOT/'deeper_new_sketchfab_cc_booth_candidates_20261106.json'
target.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('FINISHED','NEW',len(rows),'STRONG',out['strong_title_count'],'BASE_EXCLUDED',len(old),'ERRORS',len(errors),'BYTES',target.stat().st_size,flush=True)
for x in rows[:30]:print('TOP',x['uid'],x['score'],x['title'][:55],x['face_count'],flush=True)
