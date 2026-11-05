"""Probe efficient single-model extraction via HTTP range from ProSceneverse tar.
No protected models, no bulk archive download. Limits every probe response to <= 2MB.
"""
import pandas as pd,requests,io,json,sys,time
from huggingface_hub import HfApi,hf_hub_url
DATASET="Stable-X/ProSceneverse"
headers={"User-Agent":"ExpoVault-ProSceneverse-licensed-booth-range-probe/1.0"}
def fetch_table(filename):
 url=hf_hub_url(DATASET,filename,repo_type="dataset")
 r=requests.get(url,timeout=(20,90),headers=headers)
 print("TABLE_FETCH",filename,r.status_code,len(r.content),r.url[:170],flush=True)
 r.raise_for_status()
 return pd.read_parquet(io.BytesIO(r.content))
df=fetch_table("shard_index.parquet")
print("INDEX_SHAPE",df.shape,"INDEX_FIELDS",list(df.columns),flush=True)
print("INDEX_FIRST",df.head(3).to_json(orient="records")[:6000],flush=True)
md=fetch_table("metadata.parquet")
print("META_SHAPE",md.shape,"META_COLUMNS",list(md.columns),flush=True)
need=["25a38668148847a3ac36c3e318545cd5","ab70bfe5d7464251b61af81558c69e54","528a15fa2877428d92df45590f31997c"]
for uid in need:
 for d,label in [(df,"INDEX"),(md,"META")]:
  mask=d.astype(str).apply(lambda col:col.str.contains(uid,regex=False)).any(axis=1)
  matches=d[mask]
  print("UID_ROW",uid,label,len(matches),matches.head(2).to_json(orient="records")[:4300],flush=True)
api=HfApi()
try:
 entries=list(api.list_repo_tree(DATASET,repo_type="dataset",path_in_repo="shards/glbs",recursive=False))
 print("SHARD_FILES",len(entries),[(e.path,getattr(e,"size",None)) for e in entries[:6]],flush=True)
except Exception as e:
 print("LIST_ERROR",repr(e)[:400],flush=True);entries=[]
if entries:
 path=entries[0].path
 url=hf_hub_url(DATASET,path,repo_type="dataset")
 try:
  head=requests.head(url,timeout=(15,50),allow_redirects=True,headers=headers)
  print("SHARD_HEAD",head.status_code,head.headers.get("content-length"),head.headers.get("accept-ranges"),head.url[:170],flush=True)
  resp=requests.get(url,headers={**headers,"Range":"bytes=0-1023"},stream=True,timeout=(15,40),allow_redirects=True)
  print("RANGE_PROBE",resp.status_code,resp.headers.get("content-range"),resp.headers.get("content-length"),resp.headers.get("accept-ranges"),resp.url[:170],flush=True)
  if resp.status_code==206:
   buf=next(resp.iter_content(1024),b"")
   print("RANGE_SAMPLE",len(buf),repr(buf[:64]),flush=True)
  else:
   print("RANGE_UNSUPPORTED_NO_DOWNLOAD",flush=True)
  resp.close()
 except Exception as e:print("RANGE_ERROR",repr(e)[:450],flush=True)
