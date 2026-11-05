"""Extract several original CC exhibition booth GLBs while scanning one public TAR shard once."""
import concurrent.futures, hashlib, io, json, os, pathlib, re, sys, tarfile, time, zipfile
import requests
from huggingface_hub import hf_hub_url
from psv_http_range import RemoteTar

shard_id=sys.argv[1]
assert re.fullmatch(r"glbs-\d{4}",shard_id),shard_id
shard_name="shards/glbs/"+shard_id+".tar"
out=pathlib.Path("output-"+shard_id);out.mkdir(exist_ok=True)
q=json.loads(pathlib.Path("psv-bulk-candidates/candidate_queue.json").read_text())["candidates"]
already=set(json.loads(pathlib.Path("catalog/bulk_import_existing_uids.json").read_text())["current_verified_drive_uids"])
bad=re.compile(r"banner|nightstand|shelving|photo.?booth|telephone.?booth|display wall|booth sign|logo booth|prop|toy|game",re.I)
strong=re.compile(r"booth|exhibition.{0,12}stand|expo|trade.{0,8}show|trade.{0,8}fair|messestand|fuar.?stand|\\bstand\\b",re.I)
possible=[r for r in q if r["shard"]==shard_name and r["scene_id"] not in already
    and int(r["tar_order"])<=600 and not bad.search(r["name"]) 
    and (strong.search(r["name"]) or int(r["quality_score"])>=9)]
possible.sort(key=lambda r:int(r["tar_order"]))
possible=possible[:7]
print("TARGETS",shard_id,len(possible),[(r["name"][:35],r["tar_order"]) for r in possible],flush=True)
selected={r["file_name"]:r for r in possible}
accepted=[];errors=[];seen=set()
def is_source_allowed(row):
    uid=row["scene_id"]
    try:
        resp=requests.get("https://api.sketchfab.com/v3/models/"+uid,timeout=16)
        if resp.ok:
            source=resp.json()
            current=(source.get("license") or {}).get("slug")
            if current not in ("by","by-sa","cc0") or not source.get("isDownloadable"):
                return False,"SKETCHFAB_CURRENT_RIGHTS_REJECTED",None
            pics=sorted((source.get("thumbnails") or {}).get("images") or [],
                        key=lambda x:abs((x.get("width") or 0)-800))
            return True,"CURRENT_LIVE_CC_AND_DOWNLOAD_CONFIRMED",pics
        return True,"ARCHIVED_CC_LICENSE_ONLY_LIVE_API_UNAVAILABLE",None
    except Exception:
        return True,"ARCHIVED_CC_LICENSE_ONLY_LIVE_API_UNAVAILABLE",None

if selected:
    tar=RemoteTar(hf_hub_url("Stable-X/ProSceneverse",shard_name,repo_type="dataset"))
    first=time.monotonic();scanned=0
    with tarfile.open(fileobj=tar,mode="r:") as archive:
        for item in archive:
            if scanned>650 or time.monotonic()-first>630:break
            scanned+=1
            row=selected.pop(item.name,None)
            if row is None:continue
            uid=row["scene_id"]
            try:
                if item.size<15000 or item.size>68000000 or not item.isfile():
                    raise ValueError("Not a reasonably sized standalone booth model")
                allowed,reason,pics=is_source_allowed(row)
                if not allowed:raise ValueError(reason)
                data=archive.extractfile(item).read()
                if data[:4]!=b"glTF" or int.from_bytes(data[4:8],"little")!=2 or int.from_bytes(data[8:12],"little")!=len(data):
                    raise ValueError("Invalid original GLB 2")
                chunk=int.from_bytes(data[12:16],"little")
                geo=json.loads(data[20:20+chunk])
                if not geo.get("meshes") or not geo.get("nodes"):raise ValueError("No meshes")
                for res in list(geo.get("images") or [])+list(geo.get("buffers") or []):
                    if res.get("uri") and not str(res["uri"]).startswith("data:"):
                        raise ValueError("GLB has missing external resources")
                digest=hashlib.sha256(data).hexdigest()
                if digest in seen:raise ValueError("Duplicate GLB bytes within this shard")
                seen.add(digest)
                credit_url={"by":"https://creativecommons.org/licenses/by/4.0/",
                            "by-sa":"https://creativecommons.org/licenses/by-sa/4.0/",
                            "cc0":"https://creativecommons.org/publicdomain/zero/1.0/"}[row["license_slug"]]
                meta={"uid":uid,"name":row["name"],"creator":row["author_username"],
                      "sketchfab_url":row["source_url"],"license":row["license_slug"],
                      "license_url":credit_url,"license_status":reason,
                      "source_dataset":"Stable-X/ProSceneverse","source_tar":shard_name,
                      "sha256":digest,"original_glb_bytes":len(data),
                      "mesh_count":len(geo["meshes"]),"face_count":row["face_count"],
                      "quality_score":row["quality_score"],
                      "production_files":"NOT AVAILABLE; original GLB source only",
                      "review_status":"SOURCE_QA_PASSED_VISUAL_REVIEW_PENDING"}
                name="PSV-"+uid+"-GLB-CC.zip"
                with zipfile.ZipFile(out/name,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
                    z.writestr("MODEL_INFO.json",json.dumps(meta,ensure_ascii=False,indent=2))
                    z.writestr("CREATOR_CREDIT.txt",row["name"]+"\nBy: "+row["author_username"]+"\n"+row["source_url"]+"\nLicense: "+credit_url+"\n")
                    z.writestr("original.glb",data)
                with zipfile.ZipFile(out/name) as z:assert z.testzip() is None
                accepted.append({**meta,"file_name":name,"zip_bytes":(out/name).stat().st_size})
                print("EXPORTED",uid,row["name"],len(data),reason,flush=True)
            except Exception as e:
                errors.append({"uid":uid,"error":str(e)[:220]})
                print("REJECT",uid,str(e)[:220],flush=True)
            if not selected:break
    for path,row in selected.items():
        errors.append({"uid":row["scene_id"],"error":"Model not found before scan cap"})
    print("SCANNED",shard_id,scanned,"SECONDS",round(time.monotonic()-first,2),flush=True)
index={"shard":shard_name,"targeted":len(possible),"exported":len(accepted),
       "models":accepted,"errors":errors}
(out/"SHARD_MANIFEST.json").write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding="utf8")
print("SHARD_COMPLETE",shard_id,len(accepted),len(errors),flush=True)
