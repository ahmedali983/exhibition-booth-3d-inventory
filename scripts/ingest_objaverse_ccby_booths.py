#!/usr/bin/env python3
"""Mirror CC-BY Sketchfab ORIGIN models already openly distributed as GLB by
AllenAI Objaverse, after independently validating live public Sketchfab licence
and download availability for each UID.

No Sketchfab player scraping, ripper, login circumvention, API-auth bypass, or
republication of store/restricted scene assets.
"""
from __future__ import annotations
import concurrent.futures as cf, hashlib, json, pathlib, requests, time, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/'catalog'/'objaverse_matched_200.json'
OUTPUT=ROOT/'assets'/'authorized-booths'
CAT=ROOT/'catalog'/'authorized_booths.json'
MAX_BYTES=50_000_000
UA={'User-Agent':'ExpoVault-CC-BY-Licensed-Booth-Mirror/1.0'}
LICENCE='https://creativecommons.org/licenses/by/4.0/'
def fetch_json(url):
 for attempt in range(3):
  try:
   r=requests.get(url,headers=UA,timeout=18);r.raise_for_status();return r.json()
  except Exception:
   if attempt==2:raise
   time.sleep(1+attempt)
def validate(row):
 uid=row['uid']
 if row['license_as_indexed']!='CC Attribution':return None
 metadata=fetch_json('https://api.sketchfab.com/v3/models/'+uid)
 licence=(metadata.get('license') or {}).get('slug')
 if licence!='by' or not metadata.get('isDownloadable'):return None
 actual=(metadata.get('user') or {}).get('username','')
 if not actual:raise ValueError('Creator attribution missing')
 url='https://huggingface.co/datasets/allenai/objaverse/resolve/main/'+row['object_path']
 with requests.get(url,headers=UA,timeout=(16,110),stream=True) as r:
  r.raise_for_status()
  advertised=int(r.headers.get('Content-Length') or 0)
  if advertised>MAX_BYTES:raise ValueError('Size cap exceeded '+str(advertised))
  chunks=[];size=0
  for piece in r.iter_content(1024*512):
   if not piece:continue
   size+=len(piece)
   if size>MAX_BYTES:raise ValueError('Streaming size cap exceeded')
   chunks.append(piece)
  data=b''.join(chunks)
 if len(data)<32 or data[:4]!=b'glTF' or int.from_bytes(data[4:8],'little')!=2 or int.from_bytes(data[8:12],'little')!=len(data) or data[16:20]!=b'JSON':
  raise ValueError('Invalid GLB 2.0 structure')
 # Reject external texture/buffer references: hosted version must not call any third party.
 marker=data.find(b'JSON')
 json_length=int.from_bytes(data[12:16],'little')
 scene_json=json.loads(data[20:20+json_length])
 for resource in list(scene_json.get('images') or [])+list(scene_json.get('buffers') or []):
  if resource.get('uri') and not str(resource['uri']).startswith('data:'):
   raise ValueError('External resource dependency not self-contained')
 OUTPUT.mkdir(exist_ok=True,parents=True)
 filename='SKFB-'+uid+'.glb'
 target=OUTPUT/filename
 target.write_bytes(data)
 return {
  'id':'SKFB-'+uid,'uid':uid,
  'name':metadata.get('name') or row['title'],
  'creator':actual,'source_creator':actual,
  'source_url':'https://sketchfab.com/3d-models/'+uid,
  'creator_url':'https://sketchfab.com/'+actual,
  'license':'CC-BY-4.0','license_url':LICENCE,
  'license_evidence_url':'https://api.sketchfab.com/v3/models/'+uid,
  'redistribution_basis':'Creative Commons Attribution 4.0; creator credit and source URL mandatory; checked via public Sketchfab API',
  'is_downloadable_verified':True,
  'archive_source':'Objaverse 1.0 / allenai/objaverse public GLB dataset',
  'archive_path':row['object_path'],
  'archive_retrieval':'https://huggingface.co/datasets/allenai/objaverse/resolve/main/'+row['object_path'],
  'kind':'booth','is_full_booth':True,'glb':'assets/authorized-booths/'+filename,
  'thumbnail':None,'file_size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
  'description':'Original creator-uploaded 3D exhibition stand, archived in Objaverse; CC BY 4.0. Credit '+actual+' and original Sketchfab model on reuse. Concept geometry only, not certified manufacturing plans.'
 }
def main():
 rows=json.loads(SOURCE.read_text(encoding='utf8'))
 allowed=[row for row in rows if row['license_as_indexed']=='CC Attribution']
 print('MATCHED',len(rows),'CC_BY_CANDIDATES',len(allowed),'SIZE_LIMIT_BYTES',MAX_BYTES,flush=True)
 existing=json.loads(CAT.read_text(encoding='utf8'))
 byid={x['id']:x for x in existing.get('assets',[])}
 results=[];failed=[]
 with cf.ThreadPoolExecutor(max_workers=4) as pool:
  fs={pool.submit(validate,row):row for row in allowed}
  for i,future in enumerate(cf.as_completed(fs),1):
   row=fs[future]
   try:
    out=future.result()
    if out:results.append(out);print('SAVED',out['id'],round(out['file_size']/1048576,2),'MiB',out['creator'],flush=True)
    else:print('SKIP',row['uid'],'not CC-BY downloadable now',flush=True)
   except Exception as e:
    failed.append({'uid':row['uid'],'error':str(e)[:200]})
    print('SKIP',row['uid'],str(e)[:200],flush=True)
   if i%4==0:print('PROGRESS',i,'/',len(fs),'NEW',len(results),'FAIL',len(failed),flush=True)
 for result in results:byid[result['id']]=result
 allassets=sorted(byid.values(),key=lambda x:(x['name'].lower(),x['id']))
 CAT.write_text(json.dumps({
  'name':'Licensed original exhibition booth GLBs hosted on ExpoVault',
  'count':len(allassets),
  'license_filter':'CC-BY-4.0 live verified only',
  'credit_rule':'Every download, edit or derivative must preserve the author, original model URL, licence URL and notice of changes.',
  'warning':'Open 3D geometry; no native SketchUp/3ds Max files or manufacturer approved engineering drawings included.',
  'assets':allassets,'last_import':{'added':len(results),'skipped':failed}
 },ensure_ascii=False,indent=2),encoding='utf8')
 print('RESULT',len(results),'files','NEW_BYTES',sum(x['file_size'] for x in results),'FAILED',len(failed),flush=True)
if __name__=='__main__':main()
