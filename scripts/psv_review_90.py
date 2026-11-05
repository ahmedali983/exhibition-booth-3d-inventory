"""Preview high-signal genuine licensed booths across open archive; do not bulk download meshes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
from io import BytesIO
import requests, re, json, time
OUT=Path("psv-booth-visual-census");OUT.mkdir(exist_ok=True)
q=json.loads(Path("psv-bulk-candidates/candidate_queue.json").read_text())["candidates"]
known=set(json.loads(Path("catalog/bulk_import_existing_uids.json").read_text())["current_verified_drive_uids"])
exclude=re.compile(r"^0[0-9]_INDA|^INDA|texture.model|RPL|lumiere|straight display|backlit display|ready pop|fabric pop|wall config|display system|nightstand|phone booth|photo booth|book stand|bus stand|exhibit.?sign|display fixture|lightbox",re.I)
good=re.compile(r"\b(?:booth|stand|pavilion|pavillion|exhibition|exposition|expo|tradeshow|trade show|fuar|messe|estande|Computex|Showroom|Molenaar|Weliba|Kahai|Kro stand|Strella|Booth)\b",re.I)
extra=re.compile(r"3d design expo|event booth|brands|promo|convention",re.I)
byuid={}
for r in q:
 uid=r["scene_id"];name=str(r.get("name") or "")
 if uid in known or exclude.search(name) or not (good.search(name) or extra.search(name)):continue
 if int(r["face_count"] or 0)<4000:continue
 row=dict(r);row["_rank"]=int(r["quality_score"])*3+min(10,int(r.get("view_count") or 0)//200)
 if re.search(r"exhibition|booth|fuar|messestand|expo|tradeshow",name,re.I):row["_rank"]+=20
 byuid[uid]=row
rows=sorted(byuid.values(),key=lambda r:(-r["_rank"],int(r["tar_order"])))[:90]
print("FILTER",len(q),"SELECTED",len(rows),flush=True)
def probe(row):
 uid=row["scene_id"];prefix="https://mirror.traines.eu/sketchfab-backup/"+uid[:2]+"/"+uid
 s=requests.Session();s.headers.update({"User-Agent":"ExpoVault-small-curated-licensed-booth-preview/1.0"})
 data={"uid":uid,"name":row["name"],"license":row["license_slug"],"creator":row["author_username"],"face_count":row["face_count"],"rank":row["_rank"],"description":str(row.get("description") or "")[:380],"caption":str(row.get("caption") or "")[:380],"source_url":row["source_url"],"shard":row["shard"],"tar_order":row["tar_order"]}
 img=None
 try:
  r=s.get(prefix+".thumb.jpeg",timeout=(8,18));r.raise_for_status()
  img=Image.open(BytesIO(r.content)).convert("RGB")
  data["preview"]=True
 except Exception as e:data["preview_error"]=str(e)[:120]
 for ext,label in [(".zip","gltf"),(".source.zip","native")]:
  try:
   r=s.head(prefix+ext,allow_redirects=True,timeout=(7,13))
   data[label+"_status"]=r.status_code
   data[label+"_bytes"]=int(r.headers.get("content-length") or 0)
  except Exception as e:data[label+"_error"]=str(e)[:120]
 return data,img
with ThreadPoolExecutor(max_workers=5) as pool:
 examined=list(pool.map(probe,rows))
results=[x[0] for x in examined]
(OUT/"review_index.json").write_text(json.dumps({"inspected":len(results),"candidate_count":len(q),"models":results},ensure_ascii=False,indent=2),encoding="utf8")
n=0
for page in range((len(examined)+19)//20):
 subset=examined[page*20:(page+1)*20]
 W,H=298,248;board=Image.new("RGB",(5*W,4*H),"white");draw=ImageDraw.Draw(board)
 for i,(r,pic) in enumerate(subset):
  x=(i%5)*W;y=(i//5)*H
  if pic is not None:
   pic.thumbnail((W-8,185));board.paste(pic,(x+(W-pic.width)//2,y+(185-pic.height)//2))
  draw.text((x+5,y+190),f"{page*20+i+1}. {r['name'][:37]}",fill=(15,15,20))
  draw.text((x+5,y+207),r["uid"],fill=(35,35,45))
  draw.text((x+5,y+224),f"GLTF {r.get('gltf_bytes',0)//1048576} MB | SOURCE {r.get('native_bytes',0)//1048576} MB",fill=(60,65,70))
 board.save(OUT/f"contact_{page+1:02d}.jpg",quality=82)
print("COMPLETED",len(results),"ORIGINAL_ZIP",sum(x.get("gltf_status")==200 for x in results),"NATIVE",sum(x.get("native_status")==200 for x in results),"SHEETS",page+1,flush=True)
for i,x in enumerate(results):
 if x.get("gltf_status")==200:print("CANDIDATE",i+1,x["uid"],x["name"][:75],x["gltf_bytes"],flush=True)
