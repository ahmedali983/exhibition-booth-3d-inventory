#!/usr/bin/env python3
"""Source/archive preflight for official-search CC exhibition booth candidates.

Metadata licensing is not a grant for every mirror: only inspect public archived assets.
No paid, view-only or protected model is fetched or added here.
"""
import concurrent.futures, json, pathlib, re, sys
from io import BytesIO
import requests
from PIL import Image, ImageDraw
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
N=4
shard=int(sys.argv[1]) if len(sys.argv)>1 else 0
assert 0 <= shard < N
data=json.loads(pathlib.Path("catalog/worldwide_licensed_booth_candidates_20261106.json").read_text(encoding="utf-8"))
rows=[x for i,x in enumerate(data["items"]) if i % N==shard]
out=pathlib.Path("worldwide-source-qa") / str(shard);out.mkdir(parents=True,exist_ok=True)
UA={"User-Agent":"ExpoVault-Open-CC-3D-Source-Availability-Audit/1.0"}
def check(row):
    session=requests.Session();session.headers.update(UA)
    session.mount("https://",HTTPAdapter(max_retries=Retry(total=2,backoff_factor=0.4,status_forcelist=[429,500,502,503,504])))
    uid=row["uid"];base=f"https://mirror.traines.eu/sketchfab-backup/{uid[:2]}/{uid}"
    result={**row}
    for key,suffix in [("gltf",".zip"),("native",".source.zip"),("thumbnail",".thumb.jpeg")]:
        try:
            r=session.head(base+suffix,timeout=(6,16),allow_redirects=True)
            result[key+"_status"]=r.status_code
            result[key+"_size"]=int(r.headers.get("Content-Length") or 0)
        except Exception as e:result[key+"_error"]=str(e)[:100]
    result["ready_glTF"]=result.get("gltf_status")==200 and result.get("gltf_size",0)>10000
    result["native_available"]=result.get("native_status")==200
    # license was read from official public API during catalog phase; revalidate at ingestion.
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results=list(pool.map(check,rows))
available=[x for x in results if x.get("ready_glTF")]
available.sort(key=lambda x:(not x["exact_title_candidate"],-x["score"],-x["faces"]))
report={"shard":shard,"count_checked":len(results),"source_glTF_available":len(available),
    "full_original_native_sources":sum(x["native_available"] for x in available),
    "previous_existing_uids":data["baseline"],
    "note":"Availability is not shape or licence acceptance. Per-file live license, unzip safety, GLB geometry, and visual booth completeness must be validated separately.",
    "source_ready":available,"unavailable": [x for x in results if not x.get("ready_glTF")]}
(out/"source_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("RESULT",shard,"CHECKED",len(results),"READY",len(available),"NATIVE",report["full_original_native_sources"],flush=True)
# Visually review the actual author thumbnails, not synthesized images.
W,H=330,250
for page in range((min(70,len(available))+19)//20):
    subset=available[page*20:page*20+20]
    board=Image.new("RGB",(4*W,5*H),"white")
    draw=ImageDraw.Draw(board)
    def load_thumb(item):
        uid=item["uid"];url=f"https://mirror.traines.eu/sketchfab-backup/{uid[:2]}/{uid}.thumb.jpeg"
        try:
            r=requests.get(url,headers=UA,timeout=(6,18));r.raise_for_status()
            img=Image.open(BytesIO(r.content)).convert("RGB");img.thumbnail((W-10,175))
            return img
        except Exception:return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:imgs=list(pool.map(load_thumb,subset))
    for i,(item,im) in enumerate(zip(subset,imgs)):
        x=i%4*W;y=i//4*H
        if im:board.paste(im,(x+(W-im.width)//2,y+(175-im.height)//2))
        draw.text((x+5,y+179),str(page*20+i+1)+". "+item["title"][:39],fill="#111111")
        draw.text((x+5,y+201),item["uid"],fill="#111111")
        draw.text((x+5,y+224),"GLTF "+str(item.get("gltf_size",0)//1048576)+"MB / NATIVE "+str(item.get("native_size",0)//1048576)+"MB",fill="#111111")
    board.save(out/f"contact_{page+1:02d}.jpg",quality=82)
