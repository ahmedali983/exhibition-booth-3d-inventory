#!/usr/bin/env python3
"""EXPOVAULT / OPEN CC0 3D INGEST

Downloads self-contained, verified CC0 glTF 2.0 (.glb) assets from the official
3DAssets.dev REST API into ExpoVault's own assets/open-3d/ storage. No sign-in,
no scraping, no bypass of access controls. The API explicitly permits rehosting.

Usage:
  python scripts/ingest_cc0_3d.py --workers 8
  python scripts/ingest_cc0_3d.py --workers 6 --max-assets 120
  python scripts/ingest_cc0_3d.py --packs art-gallery-and-exhibition-rooms

Fresh records only enter the production catalogue once the GLB has been
downloaded, checked for glTF 2.0 magic/length and stored successfully.
"""
from __future__ import annotations
import argparse
import concurrent.futures as futures
import hashlib
import json
import os
import pathlib
import random
import re
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT=pathlib.Path(__file__).resolve().parents[1]
ASSET_DIR=ROOT/"assets"/"open-3d"
CATALOG=ROOT/"catalog"/"open_3d_cc0.json"
PACKS=[
 "art-gallery-and-exhibition-rooms",
 "retail-store-fixtures-and-mall",
 "indoor-market-hall-and-traders",
 "village-hall-and-community-events",
 "opticians-and-eyewear-showroom",
 "trading-post-and-barter-market",
 "hardware-store-and-diy-warehouse",
]
USER_AGENT="ExpoVault-CC0-3D-Ingestion/1.0 (github.com/ahmedali983/exhibition-booth-3d-inventory)"
MAX_FILE=20_000_000
def get(url,max_bytes=2_000_000):
    req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json,image/webp,model/gltf-binary,*/*"})
    with urlopen(req,timeout=17) as res:
        if res.status!=200:raise ValueError(f"HTTP {res.status} {url}")
        data=res.read(max_bytes+1)
        if len(data)>max_bytes:raise ValueError(f"File too large {url}")
        return data
def allow(url,host):
    try:
        p=urlparse(url)
        return p.scheme=="https" and p.hostname==host and not p.username and not p.password
    except Exception:return False
def record(item,pack):
    license_data=item.get("license") or {}
    if license_data.get("slug")!="cc0-1.0" or license_data.get("attributionRequired") is not False:return None
    url=item.get("cdnUrl") or ""
    thumb=item.get("thumbnailUrl") or ""
    if not allow(url,"cdn.3dassets.dev") or not allow(thumb,"cdn.3dassets.dev"):return None
    identity=str(item.get("id",""))
    if not identity.isdigit():return None
    size=int((item.get("stats") or {}).get("fileSize") or 0)
    if size<100 or size>MAX_FILE:return None
    return {
        "id":"CC0-"+identity,"name":item.get("title") or identity,
        "pack":pack["title"],"pack_slug":pack["slug"],
        "kind":item.get("category",{}).get("title","3D design asset"),
        "description":(item.get("summary") or "")[:430],
        "source_url":item.get("url"),"license":"CC0-1.0",
        "source_creator":(item.get("contributor") or {}).get("name") or "3DAssets.dev",
        "ai_generated":bool(item.get("aiGenerated")),
        "file_size":size,"triangles":int((item.get("stats") or {}).get("triangles") or 0),
        "source_glb":url,"source_thumb":thumb,
        "glb":"assets/open-3d/CC0-"+identity+".glb",
        "thumbnail":"assets/open-3d/CC0-"+identity+".webp",
    }
def validated_glb(data):
    if len(data)<20 or data[:4]!=b"glTF" or int.from_bytes(data[4:8],"little")!=2:
        raise ValueError("Not a glTF v2 binary")
    declared=int.from_bytes(data[8:12],"little")
    if declared!=len(data):raise ValueError(f"Invalid GLB length {declared} != {len(data)}")
    if data[16:20]!=b"JSON":raise ValueError("GLB JSON scene header missing")
    return True
def transfer(asset,attempts=3):
    ASSET_DIR.mkdir(exist_ok=True,parents=True)
    glb=ROOT/asset["glb"];thumb=ROOT/asset["thumbnail"]
    if glb.exists():
        try:
            data=glb.read_bytes();validated_glb(data)
            asset["sha256"]=hashlib.sha256(data).hexdigest()
            has_glb=True
        except Exception:
            glb.unlink(missing_ok=True);has_glb=False
    else:has_glb=False
    if not has_glb:
        for trial in range(attempts):
            try:
                data=get(asset["source_glb"],MAX_FILE);validated_glb(data)
                glb.with_suffix(".tmp").write_bytes(data)
                os.replace(glb.with_suffix(".tmp"),glb)
                asset["sha256"]=hashlib.sha256(data).hexdigest()
                break
            except Exception:
                if trial==attempts-1:raise
                time.sleep((trial+1)*.7+random.random()*.5)
    if not thumb.exists():
        for trial in range(2):
            try:
                pic=get(asset["source_thumb"],900_000)
                if pic[:4]!=b"RIFF" or pic[8:12]!=b"WEBP":
                    raise ValueError("Invalid WebP thumbnail")
                thumb.with_suffix(".tmp").write_bytes(pic)
                os.replace(thumb.with_suffix(".tmp"),thumb)
                break
            except Exception:
                if trial==1:asset["thumbnail"]=None
                else:time.sleep(.7)
    return asset
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packs",nargs="*",default=PACKS)
    ap.add_argument("--max-assets",type=int,default=0)
    ap.add_argument("--workers",type=int,default=7)
    args=ap.parse_args()
    selected=[];failures=[];packs_meta=[]
    for slug in args.packs:
        if not re.fullmatch(r"[a-z0-9-]{4,90}",slug):raise ValueError("Invalid pack identifier")
        url="https://3dassets.dev/api/v1/packs/"+slug
        d=None
        for trial in range(4):
            try:
                d=json.loads(get(url,1_500_000).decode("utf-8"))["data"]
                break
            except Exception as error:
                print("MANIFEST_RETRY",slug,trial+1,str(error)[:110],flush=True)
                time.sleep(1+trial*1.5)
        if d is None:
            failures.append({"pack":slug,"error":"Manifest unavailable after retries"})
            continue
        pack={"slug":slug,"title":d["title"],"license":d.get("licenseLabel"),"available":len(d.get("assets") or [])}
        if pack["license"]!="CC0 1.0 Universal":raise ValueError("Non-CC0 pack: "+slug)
        packs_meta.append(pack)
        for source in d.get("assets") or []:
            candidate=record(source,{"title":d["title"],"slug":slug})
            if candidate:selected.append(candidate)
        print("PACK",slug,"eligible",len(d.get("assets") or []),flush=True)
    selected=list({v["id"]:v for v in selected}.values())
    if args.max_assets: selected=selected[:args.max_assets]
    print("TO_FETCH",len(selected),"WITH",max(1,min(10,args.workers)),"workers",flush=True)
    installed=[]
    with futures.ThreadPoolExecutor(max_workers=max(1,min(10,args.workers))) as pool:
        completed={pool.submit(transfer,item):item for item in selected}
        for i,future in enumerate(futures.as_completed(completed),1):
            try:installed.append(future.result())
            except Exception as e:failures.append({"id":completed[future]["id"],"error":str(e)[:200]})
            if i%40==0 or i==len(selected):
                print("PROGRESS",i,"/",len(selected),"saved",len(installed),"failed",len(failures),flush=True)
    installed.sort(key=lambda v:(v["pack_slug"],v["name"].lower()))
    result={
        "title":"ExpoVault Self-Hosted Open 3D Assets",
        "license":"CC0-1.0",
        "disclaimer":"These are separate source-authored scene components and props, not certified exhibition booth shop drawings.",
        "source":"3DAssets.dev official API; CC0 direct downloadable immutable GLBs",
        "count":len(installed),"bytes":sum(v["file_size"] for v in installed),
        "packs":packs_meta,"assets":installed,"failures":failures
    }
    CATALOG.parent.mkdir(parents=True,exist_ok=True)
    CATALOG.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("RESULT",len(installed),"saved GLBs",len(failures),"failed","total bytes",sum(v["file_size"] for v in installed),flush=True)
    if failures:print("ERRORS",json.dumps(failures[:12]),flush=True)
if __name__=="__main__":main()
