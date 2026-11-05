#!/usr/bin/env python3
"""Extract specific CC exhibition booth GLBs from multi-GB ProSceneverse TARs.
HTTP-Range-only, independent original models, no 15GB shard downloads.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from io import BytesIO
import json,re,hashlib,zipfile,requests,time,os,math
import pandas as pd
from huggingface_hub import hf_hub_url

REPO="Stable-X/ProSceneverse"
OUT=Path("prosceneverse-selective-source")
OUT.mkdir(exist_ok=True)
USER_AGENT="ExpoVault-CC-Scene-Batch-HTTP-Range/1.0 (selective open dataset)"
PAT=re.compile(r"\b(?:exhibition\s+(?:booth|stand|stall)|expo\s+(?:booth|stand|stall)|trade[- ]?show\s+(?:booth|stand)|tradeshow\s+(?:booth|stand)|exhibit(?:ion)?\s+(?:booth|stand)|booth\s+(?:exhibit|design)|fair\s+stand|showroom\s+booth|exposition\s+stand)\b",re.I)
BAD=re.compile(r"(?:no debe ser utilizado|without authorization|do not use|noncommercial|not permitted|not for use|copyrighted\s+model)",re.I)
HEAD=512
def table(path):
 r=requests.get(hf_hub_url(REPO,path,repo_type="dataset"),timeout=(10,95))
 r.raise_for_status()
 return pd.read_parquet(BytesIO(r.content))
md=table("metadata.parquet")
idx=table("shard_index.parquet")
idx=idx[idx["path"].str.endswith(".glb")].copy()
idx=idx.sort_values(["shard","path"])
idx["order_in_shard"]=idx.groupby("shard").cumcount()
df=md.merge(idx,left_on="file_name",right_on="path",how="inner")
df=df[df.license_slug.isin(["by","cc0","by-sa"])]
df=df[df.name.fillna("").str.contains(PAT,regex=True) | df.description.fillna("").str.contains(PAT,regex=True)]
df=df[~df.description.fillna("").str.contains(BAD,regex=True)]
df=df[(df.face_count>4000)&(df.face_count<700000)]
df=df.sort_values(["order_in_shard","view_count"],ascending=[True,False])
# Only one original model per TAR initially, the fastest proof-of-extraction.
selected=[];shards=set()
for _,r in df.iterrows():
 if r.shard in shards or r.order_in_shard>110:continue
 selected.append({k:(r[k].item() if hasattr(r[k],"item") else r[k]) for k in ["scene_id","name","source_url","license_slug","author_username","description","face_count","file_name","shard","order_in_shard","category"]})
 shards.add(r.shard)
 if len(selected)>=6:break
print("LICENSED_QUALIFIED",len(df),"FAST_SHARD_SELECTION",json.dumps(selected,ensure_ascii=False)[:7500],flush=True)
(OUT/"selection.json").write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding="utf8")
def octal(b):
 b=b.split(b"\0",1)[0].strip()
 if not b:return 0
 if b[0]&128:return int.from_bytes(b,"big")&((1<<(8*len(b)-1))-1)
 return int(b,8)
def download_one(m):
 shard=m["shard"];target=m["file_name"];uid=m["scene_id"]
 sess=requests.Session();sess.headers["User-Agent"]=USER_AGENT
 raw=hf_hub_url(REPO,shard,repo_type="dataset")
 check=sess.head(raw,timeout=(10,40),allow_redirects=True)
 check.raise_for_status()
 url=check.url
 total=int(check.headers["content-length"])
 def portion(start,length):
  if start<0 or length<1 or start+length>total:raise RuntimeError("invalid byte range")
  h={"Range":f"bytes={start}-{start+length-1}"}
  r=sess.get(url,headers=h,stream=True,timeout=(10,40),allow_redirects=True)
  if r.status_code!=206:
   r.close()
   raise RuntimeError("Range unsupported or changed status "+str(r.status_code))
  cl=r.headers.get("content-range") or ""
  if not cl.startswith(f"bytes {start}-{start+length-1}/"):
   r.close();raise RuntimeError("unexpected Content-Range "+cl[:120])
  data=bytearray()
  for chunk in r.iter_content(1024*1024):
   data.extend(chunk)
   if len(data)>length:raise RuntimeError("Range exceeded expected")
  r.close()
  if len(data)!=length:raise RuntimeError("Truncated HTTP Range")
  return bytes(data)
 offset=0
 start=time.monotonic()
 seen=0
 while offset+512<=total and seen<130 and time.monotonic()-start<290:
  block=portion(offset,HEAD)
  if not block.strip(b"\0"):break
  name=block[:100].split(b"\0",1)[0].decode("utf8","replace")
  prefix=block[345:500].split(b"\0",1)[0].decode("utf8","replace")
  name=prefix+"/"+name if prefix else name
  size=octal(block[124:136])
  if size<0 or size>500_000_000 or offset+512+size>total:raise RuntimeError("Invalid TAR header size at "+str(offset))
  if name==target:
   if size>85_000_000:raise RuntimeError("GLB exceeds first batch size limit "+str(size))
   glb=portion(offset+512,size)
   if glb[:4]!=b"glTF" or int.from_bytes(glb[4:8],"little")!=2 or int.from_bytes(glb[8:12],"little")!=len(glb):
    raise RuntimeError("GLB 2.0 header invalid")
   chunk_size=int.from_bytes(glb[12:16],"little")
   scene=json.loads(glb[20:20+chunk_size])
   if not scene.get("meshes") or not scene.get("nodes"):raise RuntimeError("No GLB geometry")
   for elem in list(scene.get("images") or [])+list(scene.get("buffers") or []):
    if elem.get("uri") and not elem["uri"].startswith("data:"):raise RuntimeError("External GLB resources")
   license=m["license_slug"]
   license_url={"by":"https://creativecommons.org/licenses/by/4.0/","by-sa":"https://creativecommons.org/licenses/by-sa/4.0/","cc0":"https://creativecommons.org/publicdomain/zero/1.0/"}[license]
   info={"uid":uid,"title":m["name"],"creator":m["author_username"],"source_url":m["source_url"],"license":license,"license_url":license_url,"archive_dataset":"https://huggingface.co/datasets/"+REPO,
     "tar_shard":shard,"tar_member":target,"tar_offset":offset,"face_count_metadata":m["face_count"],"mesh_count":len(scene["meshes"]),"glb_bytes":len(glb),"glb_sha256":hashlib.sha256(glb).hexdigest(),"production_file":"NOT_AVAILABLE","note":"Original model geometry. 3D source GLB is not certified fabrication drawings. Individual CC rights and author attribution preserved."}
   path=OUT/("PSC-"+uid+"-ORIGINAL-GLB.zip")
   with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    z.writestr("MODEL_INFORMATION.json",json.dumps(info,ensure_ascii=False,indent=2))
    z.writestr("ATTRIBUTION.txt",f"{m['name']}\nCreator: {m['author_username']}\nOriginal: {m['source_url']}\nLicense: {license} {license_url}\nConverted: No. Direct original GLB from ProSceneverse dataset.\n")
    z.writestr("original_scene.glb",glb)
   with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    assert hashlib.sha256(z.read("original_scene.glb")).hexdigest()==info["glb_sha256"]
   return {"uid":uid,"title":m["name"],"source":m["source_url"],"zip":path.name,"archive_size":path.stat().st_size,**info}
  offset+=HEAD+((size+HEAD-1)//HEAD)*HEAD
  seen+=1
  if seen%25==0:print("HEADER_PROGRESS",uid,seen,"elapsed",round(time.monotonic()-start,1),flush=True)
 raise RuntimeError(f"Could not locate original tar member {target} after {seen} headers; shard {shard} at offset {offset}")
results=[];errors=[]
with ThreadPoolExecutor(max_workers=3) as executor:
 futures={executor.submit(download_one,m):m for m in selected}
 for f in as_completed(futures):
  m=futures[f]
  try:
   result=f.result();results.append(result);print("EXTRACTED",result["uid"],result["title"][:70],result["glb_bytes"],flush=True)
  except Exception as e:
   errors.append({"uid":m["scene_id"],"title":m["name"],"error":str(e)[:300]})
   print("FAILED",m["scene_id"],str(e)[:300],flush=True)
(OUT/"EXTRACTION_INDEX.json").write_text(json.dumps({"attempted":len(selected),"success":len(results),"models":results,"errors":errors},ensure_ascii=False,indent=2),encoding="utf8")
print("BATCH_COMPLETE",len(results),len(errors),flush=True)
if not results:raise RuntimeError("No tar GLB extracted")
