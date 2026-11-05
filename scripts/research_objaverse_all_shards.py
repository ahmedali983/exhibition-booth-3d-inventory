#!/usr/bin/env python3
"""Census all openly downloadable, per-model CC BY or CC0 Sketchfab 3D files
in the ~800k-model Objaverse-1.0 annotations. Index metadata ONLY; a candidate
is NOT a hosted GLB. Local download requires licence revalidation.
"""
from pathlib import Path
import concurrent.futures as futures,gzip,json,re,requests,tempfile,time,collections
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'catalog'
UA={'User-Agent':'ExpoVault-Permitted-3D-Research/1.0'}
api='https://huggingface.co/api/datasets/allenai/objaverse/tree/main/metadata?limit=500'
resp=requests.get(api,headers=UA,timeout=25);resp.raise_for_status()
paths=sorted(x['path'] for x in resp.json() if str(x.get('path','')).endswith('.json.gz'))
print('SHARDS',len(paths),flush=True)
if len(paths)<100:raise RuntimeError('Incomplete HuggingFace shard listing')
booth=re.compile(r'\b(?:exhibition[\s_-]*(?:booth|stand|stall)|expo[\s_-]*(?:booth|stand|pavilion)|trade[\s_-]*(?:show|fair)[\s_-]*(?:booth|stand)|tradeshow[\s_-]*(?:booth|stand)|(?:exhibition|expo|tradeshow|trade[\s_-]*fair)[\s_-]*(?:design|setup)|(?:booth|stand)[\s_-]*design|exhibit[\s_-]*booth)\b',re.I)
relevant=re.compile(r'\b(?:exhibition|expo|tradeshow|trade[\s_-]*show|trade[\s_-]*fair|showroom|pavilion|display[\s_-]*stand|exhibit|conference[\s_-]*booth|event[\s_-]*booth|kiosk|retail[\s_-]*counter|pop[\s_-]*up[\s_-]*shop)\b',re.I)
item=re.compile(r'\b(?:display[\s_-]*(?:case|cabinet|stand|rack|shelf|counter|panel|wall)|information[\s_-]*(?:stand|counter|kiosk)|banner[\s_-]*stand|reception[\s_-]*(?:desk|counter)|brochure[\s_-]*(?:rack|stand)|product[\s_-]*display|podium|plinth|spotlight|truss[\s_-]*system)\b',re.I)
def process(path):
 url='https://huggingface.co/datasets/allenai/objaverse/resolve/main/'+path
 failure=None
 for attempt in range(3):
  try:
   data=requests.get(url,headers=UA,timeout=28);data.raise_for_status()
   d=json.loads(gzip.decompress(data.content))
   out=[];counts=collections.Counter()
   for uid,meta in d.items():
    counts['total']+=1
    if not meta.get('isDownloadable'):continue
    license=(meta.get('license') or {})
    slug=license.get('slug') if isinstance(license,dict) else (license if isinstance(license,str) else '')
    if slug not in ('by','cc0'):continue
    counts['license_eligible']+=1
    title=str(meta.get('name') or '')
    desc=str(meta.get('description') or '')
    if booth.search(title) or booth.search(desc):
     category='EXACT_BOOTH_CANDIDATE';score=120+ (10 if booth.search(title) else 0)
    elif relevant.search(title):
     category='RELATED_EXHIBITION_OR_RETAIL_SCENE';score=70
    elif item.search(title):
     category='MODULAR_DISPLAY_ITEM';score=50
    elif relevant.search(desc):
     category='WEAK_METADATA_MATCH';score=25
    else:continue
    counts[category]+=1
    user=(meta.get('user') or {})
    creator=(user.get('username') if isinstance(user,dict) else '') or ''
    out.append({'uid':uid,'title':title[:240],'creator':creator,'license':slug,'category':category,'score':score,
       'original_url':meta.get('viewerUrl') or 'https://sketchfab.com/models/'+uid,'availability':'ARCHIVED_DATASET_METADATA_ONLY_NOT_HOSTED',
       'archive_hint':path,'views':meta.get('viewCount',0)})
   return counts,out,None
  except Exception as e:
   failure=str(e)[:180];time.sleep(attempt+1)
 return collections.Counter(),[],path+' '+str(failure)
summary=collections.Counter();rows=[];failures=[]
with futures.ThreadPoolExecutor(max_workers=8) as pool:
 tasks={pool.submit(process,p):p for p in paths}
 for i,f in enumerate(futures.as_completed(tasks),1):
  counts,candidates,failure=f.result()
  summary.update(counts);rows.extend(candidates)
  if failure:failures.append(failure)
  if i%25==0 or i==len(paths):
   print('PROGRESS',i,'/',len(paths),'VALID',summary['license_eligible'],'BOOTH',summary['EXACT_BOOTH_CANDIDATE'],'RELATED',summary['RELATED_EXHIBITION_OR_RETAIL_SCENE'],'ITEM',summary['MODULAR_DISPLAY_ITEM'],'ERRORS',len(failures),flush=True)
rows.sort(key=lambda x:(-x['score'],-int(x['views'] or 0),x['uid']))
summary_doc={'source':'allenai/objaverse metadata, public Sketchfab-origin Creative Commons objects','record_count':summary['total'],
'downloadable_cc_by_or_cc0':summary['license_eligible'],
'booth_metadata_candidates':summary['EXACT_BOOTH_CANDIDATE'],
'exhibition_related_scene_candidates':summary['RELATED_EXHIBITION_OR_RETAIL_SCENE'],
'modular_display_item_candidates':summary['MODULAR_DISPLAY_ITEM'],
'weak_metadata_matches':summary['WEAK_METADATA_MATCH'],
'checked_shards':len(paths),'failed_shards':failures,
'warning':'Licence and downloadable status were saved at archive collection time. Check live licence/rights and file presence before copying; these metadata are NOT hosted model files.',
'full_index':'catalog/objaverse_cc_by_cc0_relevant_candidates.jsonl',
'examples':rows[:70]}
(OUT/'objaverse_all_800k_census.json').write_text(json.dumps(summary_doc,ensure_ascii=False,indent=2),encoding='utf8')
with (OUT/'objaverse_cc_by_cc0_relevant_candidates.jsonl').open('w',encoding='utf8') as f:
 for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
print('FINISHED',json.dumps(summary_doc)[:1100],flush=True)
