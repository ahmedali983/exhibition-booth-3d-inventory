#!/usr/bin/env python3
"""Import a manually reviewed set of clearly differentiated exhibition GLBs
from open Objaverse archive, checking current Sketchfab CC BY rights.
No ripping, bypassing login, or copying view-only assets.
"""
import concurrent.futures as cf,hashlib,json,pathlib,requests,io,time
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'/'authorized-booths'
CAT=ROOT/'catalog'/'authorized_booths.json'
URL='https://creativecommons.org/licenses/by/4.0/'
ARCHIVE='https://huggingface.co/datasets/allenai/objaverse/resolve/main/'
uids=[
 '547afebba737485ca855f90483955248', # 2020 corporate exhibition
 'd30d323be9614a7f8dd851a12464e06a', # booth with actual counter / seating
 'e482030317ca4e1a939cffd3287aeb22', # SPIE trade fair booth
 '5bf1ae45aac84838a3a64a30a508880d', # T3CUBE architectural system
]
headers={'User-Agent':'ExpoVault-Curated-Open-Exhibition-Model-Importer/1.0'}
discovery=json.loads((ROOT/'catalog'/'new_real_booth_discovery_20261105.json').read_text(encoding='utf8'))
source={x['uid']:x for x in discovery['entries']}
# T3CUBE and SPIE may not have been in the focused search index.
import gzip,tempfile
with gzip.open(pathlib.Path(tempfile.gettempdir())/'expovault_objaverse_object_paths.json.gz','rt',encoding='utf8') as f:
 archive_paths=json.load(f)
def validate_glb(data):
 if len(data)<20 or data[:4]!=b'glTF' or int.from_bytes(data[4:8],'little')!=2 or int.from_bytes(data[8:12],'little')!=len(data) or data[16:20]!=b'JSON':
  raise ValueError('Not a valid GLB 2.0')
 n=int.from_bytes(data[12:16],'little')
 obj=json.loads(data[20:20+n])
 if not obj.get('meshes'):raise ValueError('Model contains no mesh geometry')
 for part in obj.get('images',[])+obj.get('buffers',[]):
  uri=part.get('uri')
  if uri and not uri.startswith('data:'):raise ValueError('External geometry or texture dependency')
 return obj
def one(uid):
 meta=requests.get('https://api.sketchfab.com/v3/models/'+uid,headers=headers,timeout=20).json()
 license=(meta.get('license') or {}).get('slug')
 if license!='by' or not meta.get('isDownloadable'):raise ValueError('Current CC BY licence or download not confirmed')
 creator=(meta.get('user') or {}).get('username')
 if not creator:raise ValueError('Missing creator')
 path=archive_paths.get(uid)
 if not path:raise ValueError('UID not in original GLB archive')
 remote=ARCHIVE+path
 with requests.get(remote,headers=headers,stream=True,timeout=(20,110)) as res:
  res.raise_for_status()
  n=int(res.headers.get('content-length') or 0)
  if n>65000000:raise ValueError('Model larger than safe hosted size')
  data=b'';size=0
  for chunk in res.iter_content(512*1024):
   size+=len(chunk)
   if size>65000000:raise ValueError('Model exceeds hosted size cap')
   data+=chunk
 gltf=validate_glb(data)
 images=sorted((meta.get('thumbnails') or {}).get('images') or [],key=lambda x:abs(x.get('width',0)-800))
 preview=None
 for im in images:
  try:
   r=requests.get(im['url'],timeout=20,headers=headers);r.raise_for_status()
   img=Image.open(io.BytesIO(r.content)).convert('RGB')
   if img.width<200:continue
   img.thumbnail((800,650))
   buf=io.BytesIO();img.save(buf,'WEBP',quality=81,method=5)
   preview=buf.getvalue();break
  except Exception:continue
 if not preview:raise ValueError('Cannot acquire a legitimate local thumbnail')
 OUT.mkdir(parents=True,exist_ok=True)
 local='SKFB-'+uid
 (OUT/(local+'.glb')).write_bytes(data)
 (OUT/(local+'.webp')).write_bytes(preview)
 title=meta.get('name') or 'Exhibition booth'
 original=meta.get('viewerUrl') or 'https://sketchfab.com/models/'+uid
 return {
  'id':local,'uid':uid,'name':title,'creator':creator,'source_creator':creator,
  'source_url':original,'creator_url':'https://sketchfab.com/'+creator,
  'license':'CC-BY-4.0','license_url':URL,
  'license_evidence_url':'https://api.sketchfab.com/v3/models/'+uid,
  'redistribution_basis':'Current public CC BY 4.0 creator licence checked; preserve designer, origin, licence and changes in derivatives',
  'is_downloadable_verified':True,'archive_source':'Objaverse 1.0 / AllenAI',
  'archive_path':path,'archive_retrieval':remote,
  'kind':'booth','is_full_booth':True,
  'glb':'assets/authorized-booths/'+local+'.glb','thumbnail':'assets/authorized-booths/'+local+'.webp',
  'file_size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
  'triangles':int(meta.get('faceCount') or 0),'mesh_count':len(gltf['meshes']),
  'description':str(meta.get('description') or title)[:600]+' | Original artist-authored CC BY 4.0 exhibition model; not fabrication-ready.'
 }
def main():
 original=json.loads(CAT.read_text(encoding='utf8'))
 indexed={x['uid']:x for x in original['assets']}
 with cf.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(one,uid):uid for uid in uids if uid not in indexed}
  for f in cf.as_completed(futures):
   uid=futures[f]
   try:
    asset=f.result();indexed[uid]=asset
    print('SAVED',asset['name'],asset['creator'],round(asset['file_size']/1048576,2),'MiB',asset['mesh_count'],'meshes',flush=True)
   except Exception as e:print('FAILED',uid,str(e)[:200],flush=True)
 original['assets']=sorted(indexed.values(),key=lambda x:x['name'].lower())
 original['count']=len(original['assets'])
 original['last_import']['new_batch']='Manual full-booth original review; 4 candidate UIDs; rights and original GLB verified'
 CAT.write_text(json.dumps(original,ensure_ascii=False,indent=2),encoding='utf8')
 print('TOTAL_BOOTH_ORIGINALS',original['count'],flush=True)
if __name__=='__main__':main()
