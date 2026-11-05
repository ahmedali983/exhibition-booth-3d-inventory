#!/usr/bin/env python3
"""Discover actual trade-show/exhibition-booth assets from a bounded sample of open CC backup directory listings.
Metadata-only; no downloading raw models, no auth bypass.
"""
import io,json,re,time,os,requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import unquote
from PIL import Image,ImageDraw
BASE="https://mirror.traines.eu/sketchfab-backup/"
# Uniformly distributed sample of directories: 1/16 of the 256 total directories.
SHARDS=["00","10","20","30","40","50","60","70","80","90","a0","b0","c0","d0","e0","f0"]
PAT=re.compile(r"(?:exhibi(?:tion|t)[-_. ]?(?:booth|stand|stall|design|pavilion)|trade[-_. ]?(?:show|fair)[-_. ]?(?:booth|stand|stall)|expo[-_. ]?(?:booth|stand|stall)|(?:booth|stall)[-_. ]?(?:design|expo|exhibition)|messestand|messebau|fuar[-_. ]?stand|выставоч|fieristic|estande[-_. ]?(?:feira|expos)|stand[-_. ]?(?:feria|exposicion|exposition)|(?:booth|stall)[-_. ]?(?:[0-9]|[a-z]+)[-_. ]?(?:design|final|booth))",re.I)
SMALL=re.compile(r"(?:phone[-_. ]?booth|photo[-_. ]?booth|dj[-_. ]?booth|ticket[-_. ]?booth|toll[-_. ]?booth|bus[-_. ]?stand|kitchen|nightstand|stand[-_. ]?alone|banner[-_. ]?stand|vr[-_. ]?chat|stand[-_. ]?user|minecraft|roblox|fortnite)",re.I)
s=requests.Session();s.headers["User-Agent"]="ExpoVault-CC-exhibition-booth-metadata-audit/1.0"
out=Path("booth-census-sample");out.mkdir(exist_ok=True)
def scan(shard):
    url=BASE+shard+"/"
    try:
        r=s.get(url,timeout=(8,32));r.raise_for_status()
        names=re.findall(r'href="([^"]+)"',r.text)
        names=[unquote(x) for x in names if ".m." in x and x.endswith(".json")]
        candidates=[]
        for name in names:
            uid=name[:32];slug=name[35:-5]
            if len(uid)==32 and re.fullmatch('[0-9a-f]{32}',uid) and PAT.search(slug) and not SMALL.search(slug):
                candidates.append({"uid":uid,"slug":slug,"mirror_meta_url":url+name,"mirror_model_zip":url+uid+".zip","mirror_source_zip":url+uid+".source.zip","mirror_thumbnail":url+uid+".thumb.jpeg","shard":shard})
        return shard,len(names),candidates,None
    except Exception as ex:return shard,0,[],str(ex)[:220]
with ThreadPoolExecutor(max_workers=3) as pool:
    fetched=list(pool.map(scan,SHARDS))
candidates=[y for shard,n,rows,err in fetched for y in rows]
print("SAMPLE_SUMMARY",json.dumps([{"shard":shard,"model_count":n,"matched":len(rows),"error":err} for shard,n,rows,err in fetched]),flush=True)
print("MATCHED",len(candidates),flush=True)
def inspect(row):
    try:
        r=s.get(row["mirror_meta_url"],timeout=(8,18));r.raise_for_status()
        j=r.json()
        lic=j.get("license") or {}
        if isinstance(lic,dict):lic=lic.get("slug") or lic.get("label") or lic.get("uid") or ""
        title=str(j.get("name") or row["slug"])
        user=j.get("user") or {}
        creator=str(user.get("username") or user.get("displayName") or "") if isinstance(user,dict) else str(user)
        return {**row,"name":title,"creator":creator,"license":lic,"downloadable_archived":True,"source_url":j.get("viewerUrl") or "https://sketchfab.com/models/"+row["uid"],
                "description":str(j.get("description") or "")[:450],"metadata_bytes":len(r.content),"verification":"archived Creative Commons metadata, needs individual rights review"}
    except Exception as ex:return {**row,"error":str(ex)[:150]}
# Inspect bounded sample up to 80 best filenames; rate controlled by low concurrency
candidates=sorted(candidates,key=lambda x: (0 if re.search("exhibition-booth|trade-show-booth|messestand|fuar-stand",x["slug"],re.I) else 1,x["uid"]))[:80]
with ThreadPoolExecutor(max_workers=3) as pool:observed=list(pool.map(inspect,candidates))
valid=[row for row in observed if row.get("name") and row.get("creator")]
report={"purpose":"Discovery only, no GLB files are included","sample_shards":SHARDS,"counts":[{"shard":x[0],"total_metadata_files":x[1],"hits":len(x[2]),"error":x[3]} for x in fetched],
        "raw_candidate_count":len(candidates),"metadata_checked":len(observed),"metadata_complete":len(valid),"candidates":observed}
(out/"candidate_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("COMPLETE_METADATA",len(valid),flush=True)
for x in valid[:45]:
 print("BOOTH_CANDIDATE",x["uid"],x["name"][:70],"LICENSE",str(x.get("license"))[:60],"ARTIST",x["creator"][:35],flush=True)
