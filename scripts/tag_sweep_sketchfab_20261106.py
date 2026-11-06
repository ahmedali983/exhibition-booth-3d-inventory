"""Rights-first original author source candidate discovery by curated Sketchfab tags.
No download, no view-only ripping, no uploading of any image or geometry.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, json, re, time, base64, subprocess
ROOT=Path(__file__).resolve().parent
tags=['exhibition-stand','exhibition-booth','exhibition','expo-booth','expo','trade-show','tradeshow',
      'trade-fair','stand-design','booth-design','event-booth','exhibition-stall',
      'exhibit','messestand','fuar-stand','3d-booth','conference-booth','exhibition-hall']
old=set()
for f in ['worldwide_licensed_booth_candidates_20261106.json','deeper_new_sketchfab_cc_booth_candidates_20261106.json']:
 p=ROOT/f
 d=json.loads(p.read_text(encoding='utf-8'))
 old.update(x['uid'] for x in (d.get('items') or d.get('results') or []))
proc=subprocess.run(['gh','api','--method','GET','repos/ahmedali983/exhibition-booth-3d-inventory/contents/catalog/expovault_known_uids_233_20261106.json','-f','ref=feature/expovault-bulk-range-prosceneverse'],capture_output=True,text=True,timeout=25)
assert proc.returncode==0,proc.stderr[:200]
old.update(json.loads(base64.b64decode(json.loads(proc.stdout)['content']))['uids'])
def scan(tag):
 s=requests.Session();s.headers['User-Agent']='ExpoVault-public-CC-booth-tag-inventory/1.0'
 url='https://api.sketchfab.com/v3/search';params={'type':'models','tags':tag,'downloadable':'true','count':24}
 arr=[];errs=[];n=0
 for page in range(25):
  try:
   r=s.get(url,params=params,timeout=(8,35))
   r.raise_for_status();d=r.json()
   arr.extend(d.get('results') or [])
   url=d.get('next');params=None;n+=1
   if not url:break
   time.sleep(.23)
  except Exception as e:
   errs.append(str(e)[:140]);break
 print('TAG',tag,'PAGES',n,'RESULTS',len(arr),'MORE',bool(url),'ERRORS',len(errs),flush=True)
 return tag,arr,errs
bad=re.compile(r'phone|photo|security|guard|dj.?booth|bus.?stop|voting.?booth|minecraft|roblox|avatar|game|chair|table|counter|pedestal|single.?sign|reception.?desk|banner|logo|nightstand|lamp|lamp.?stand|material.?board|abstract.?sculpture',re.I)
strong=re.compile(r'exhibition.{0,14}(stand|booth|stall)|tradeshow|trade.?show.{0,14}(booth|stand)|expo.{0,14}(stand|booth|pavilion)|fuar.?stand|messestand|stand de feria|exhibit.*booth|stand design',re.I)
records={};errors=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 tasks=[pool.submit(scan,t) for t in tags]
 for f in as_completed(tasks):
  tag,rows,err=f.result();errors.extend([{'tag':tag,'error':x} for x in err])
  for d in rows:
   uid=d.get('uid') or ''
   title=d.get('name') or ''
   if not re.fullmatch('[a-f0-9]{32}',uid) or uid in old or bad.search(title):continue
   if not d.get('isDownloadable') or d.get('isAgeRestricted'):continue
   lic=str((d.get('license') or {}).get('label') or '').lower()
   if any(x in lic for x in ('noncommercial','no derivatives')):continue
   if not any(x in lic for x in ('attribution','public domain','cc0')):continue
   creator=(d.get('user') or {}).get('username') or ''
   desc=re.sub('<[^>]+>',' ',str(d.get('description') or ''))[:600]
   faces=int(d.get('faceCount') or 0)
   score=(90 if strong.search(title) else 0)+(25 if any(x in title.lower() for x in ['booth','exhibition','expo','stall','trade show']) else 0)+(10 if faces>10000 else 0)+min(20,int(d.get('likeCount') or 0)//5)
   item=records.setdefault(uid,{'uid':uid,'title':title,'creator':creator,'description':desc,'archived_license':lic,'source_url':d.get('viewerUrl') or 'https://sketchfab.com/models/'+uid,'face_count':faces,'likes':d.get('likeCount') or 0,'tags_found':[],'score':score})
   if tag not in item['tags_found']:item['tags_found'].append(tag)
data={'baseline_excluded_ids':len(old),'tags_swept':tags,'distinct_new_metadata_count':len(records),'scored_strong_title':sum(x['score']>=90 for x in records.values()),'errors':errors,'items':sorted(records.values(),key=lambda x:(-x['score'],-x['likes'])),'warning':'Metadata only; rights and full booth geometry not validated.'}
target=ROOT/'new_tagged_licensed_expo_booth_candidates_20261106.json'
target.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('FINISHED_TAG_SWEEP',len(records),'STRONG',data['scored_strong_title'],'ERRORS',len(errors),'BYTES',target.stat().st_size,flush=True)
for x in data['items'][:35]:print('TOP',x['uid'],x['score'],x['title'][:55],x['creator'],flush=True)
