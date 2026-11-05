#!/usr/bin/env python3
"""Discover *actual* exhibition booth/source-authored models, not generic 3D props.
This is public catalogue metadata discovery only, no viewer ripping.
"""
from pathlib import Path
import concurrent.futures as cf,collections,gzip,json,re,requests,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
ROOT.joinpath('catalog').mkdir(exist_ok=True)
queries=[
 'exhibition booth','exhibition stand','expo stall','expo stand','trade show booth',
 'trade show stand','exhibition stall','exhibition pavilion','exhibit booth',
 'exhibition kiosk','booth design','trade fair stand','exhibition stand design',
 'conference expo booth','modular exhibition stand','island exhibition booth',
 'custom exhibition booth','exhibition fair booth','exhibition booth design'
]
bad=re.compile(r'\b(?:dj booth|photo booth|security booth|voting booth|guard booth|phone booth|ticket booth|sound booth|game|anime|weapon|shower|medieval|casino|minecraft|roblox|fantasy|toilet|photobooth)\b',re.I)
good=re.compile(r'\b(?:exhibiti\w*|tradeshow|trade show|trade fair|expo|convention|stall|stand|booth)\b',re.I)
headers={'User-Agent':'ExpoVault-Original-3D-Booth-Discovery/1.0'}
def collect(q):
 found=[];u='https://api.sketchfab.com/v3/search';params={'type':'models','q':q,'downloadable':'true','count':24}
 for n in range(4):
  try:
   r=requests.get(u,params=params,timeout=25,headers=headers);r.raise_for_status()
   d=r.json();items=d.get('results') or []
   found.extend(items)
   u=d.get('next');params=None
   if not u:break
   time.sleep(.16)
  except Exception as e:
   print('QUERY_ERROR',repr(q),str(e)[:130],flush=True);break
 return q,found
records={}
with cf.ThreadPoolExecutor(max_workers=4) as pool:
 for q,items in pool.map(collect,queries):
  print('SEARCH',repr(q),len(items),flush=True)
  for i in items:
   uid=str(i.get('uid') or '')
   title=str(i.get('name') or '')
   if len(uid)!=32 or not good.search(title) or bad.search(title):continue
   entry=records.setdefault(uid,{'uid':uid,'title':title,'terms':[],'source_url':i.get('viewerUrl') or 'https://sketchfab.com/models/'+uid,'likes':i.get('likeCount') or 0,'views':i.get('viewCount') or 0,'description':str(i.get('description') or '')[:500]})
   if q not in entry['terms']:entry['terms'].append(q)
with gzip.open(Path(tempfile.gettempdir())/'expovault_objaverse_object_paths.json.gz','rt',encoding='utf8') as f:available=json.load(f)
for v in records.values():
 v['in_source_archive']=v['uid'] in available
 v['archive_glb_path']=available.get(v['uid'])
 v['stage']='METADATA_NOT_VERIFIED'
 v['looks_like_complete_booth']=bool(re.search(r'\b(?:exhibition|trade show|trade fair|expo|convention)\b',v['title'],re.I) and re.search(r'\b(?:booth|stall|stand|pavilion)\b',v['title'],re.I))
ordered=sorted(records.values(),key=lambda r:(not r['looks_like_complete_booth'],not r['in_source_archive'],-len(r['terms']),-r['views']))
(ROOT/'catalog'/'new_real_booth_discovery_20261105.json').write_text(json.dumps({'count':len(ordered),'archive_matched':sum(x['in_source_archive'] for x in ordered),'strong_title_matches':sum(x['looks_like_complete_booth'] for x in ordered),'entries':ordered},ensure_ascii=False,indent=2),encoding='utf8')
print('SUMMARY_TOTAL',len(ordered),'STRONG',sum(x['looks_like_complete_booth'] for x in ordered),'ARCHIVED',sum(x['in_source_archive'] for x in ordered),flush=True)
print('TOP40_ARCHIVED',[(x['title'],x['uid'],x['views']) for x in ordered if x['in_source_archive']][:40],flush=True)
