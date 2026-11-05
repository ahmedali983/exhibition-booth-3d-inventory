import io, json, re, tarfile, zipfile, hashlib, pathlib, concurrent.futures
import pandas as pd
import requests
from huggingface_hub import hf_hub_url

REPO="Stable-X/ProSceneverse"
OUT=pathlib.Path("psv-export"); OUT.mkdir(exist_ok=True)
GOOD=re.compile(r"exhibition.{0,15}(booth|stand)|expo.{0,10}(booth|stand)|trade.{0,8}(show|fair).{0,14}(booth|stand)",re.I)
BAD=re.compile(r"without authorization|no debe ser utilizado|photo booth|phone booth|non-commercial",re.I)

def parquet(file):
    r=requests.get(hf_hub_url(REPO,file,repo_type="dataset"),timeout=90)
    r.raise_for_status()
    return pd.read_parquet(io.BytesIO(r.content))

class RemoteTar(io.RawIOBase):
    def __init__(self, url):
        self.pos=0
        r=requests.head(url,allow_redirects=True,timeout=35)
        r.raise_for_status()
        self.url=r.url
        self.length=int(r.headers["Content-Length"])
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        if whence==0:self.pos=offset
        elif whence==1:self.pos+=offset
        else:self.pos=self.length+offset
        return self.pos
    def read(self,n=-1):
        if self.pos>=self.length:return b""
        if n<0:n=self.length-self.pos
        n=min(n,self.length-self.pos)
        if n==0:return b""
        s=self.pos;e=s+n-1
        r=requests.get(self.url,headers={"Range":f"bytes={s}-{e}"},timeout=(20,90))
        if r.status_code!=206:raise IOError(f"Expected partial content, got {r.status_code}")
        if not r.headers.get("Content-Range","").startswith(f"bytes {s}-{e}/"):
            raise IOError("Invalid range response")
        if len(r.content)!=n:raise IOError("Truncated response")
        self.pos+=n
        return r.content

index=parquet("shard_index.parquet")
index=index[index.path.str.endswith(".glb")]
index=index.sort_values(["shard","path"])
index["position"]=index.groupby("shard").cumcount()
md=parquet("metadata.parquet")
df=md.merge(index,left_on="file_name",right_on="path")
df=df[df.license_slug.isin(["by","cc0","by-sa"])]
df=df[(df.name.fillna("").str.contains(GOOD))|(df.description.fillna("").str.contains(GOOD))]
df=df[~df.description.fillna("").str.contains(BAD)]
df=df[(df.face_count>=3500)&(df.face_count<=600000)]
df=df[df.position<110].sort_values("position")
selected=df.drop_duplicates("shard").head(5)
print("CANDIDATES",len(df),"SHARD_SELECTION",len(selected),flush=True)
def fetch(row):
    uid=row.scene_id; shard=row.shard; member=row.file_name
    assert re.fullmatch("[a-f0-9]{32}",uid)
    fileobj=RemoteTar(hf_hub_url(REPO,shard,repo_type="dataset"))
    print("BEGIN",uid,row.name,shard,int(row.position),flush=True)
    with tarfile.open(mode="r:",fileobj=fileobj) as archive:
        for i,entry in enumerate(archive):
            if i>125:raise RuntimeError("Scanning cap reached")
            if entry.name!=member:continue
            if not entry.isfile() or entry.size>65000000:raise RuntimeError("Not regular GLB or too large")
            data=archive.extractfile(entry).read()
            if data[:4]!=b"glTF" or int.from_bytes(data[8:12],"little")!=len(data):
                raise RuntimeError("Invalid original GLB")
            n=int.from_bytes(data[12:16],"little")
            scene=json.loads(data[20:20+n])
            if not scene.get("meshes"):raise RuntimeError("Empty geometry")
            info={"uid":uid,"title":row["name"],"creator":row.author_username,
              "license":row.license_slug,"source":row.source_url,"dataset":REPO,
              "original_tar_member":member,"sha256":hashlib.sha256(data).hexdigest(),
              "bytes":len(data),"mesh_count":len(scene["meshes"]),
              "engineering_production_files":"NOT SUPPLIED"}
            target=OUT/("PSV-"+uid+"-ORIGINAL-GLB.zip")
            with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
                z.writestr("MODEL_INFORMATION.json",json.dumps(info,ensure_ascii=False,indent=2))
                z.writestr("ATTRIBUTION.txt",f"Creator: {row.author_username}\nOriginal: {row.source_url}\nLicense: {row.license_slug}\n")
                z.writestr("original.glb",data)
            with zipfile.ZipFile(target) as z:
                assert z.testzip() is None
            print("EXTRACTED",uid,int(row.position),len(data),target.stat().st_size,flush=True)
            return info
    raise RuntimeError("Source model not in shard")
success=[];fail=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    tasks={pool.submit(fetch,row):row for _,row in selected.iterrows()}
    for fut in concurrent.futures.as_completed(tasks):
        row=tasks[fut]
        try:success.append(fut.result())
        except Exception as e:
            fail.append({"uid":row.scene_id,"message":str(e)[:240]})
            print("FAILED",row.scene_id,str(e)[:240],flush=True)
(OUT/"BATCH_INDEX.json").write_text(json.dumps({"success":success,"fail":fail},indent=2))
print("TOTAL",len(success),len(fail),flush=True)
