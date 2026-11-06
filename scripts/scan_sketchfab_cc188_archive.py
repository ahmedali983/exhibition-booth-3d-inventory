"""Inspect publicly available artist-licensed Sketchfab creator assets using UID lookups, not private model ripping."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import requests,json,re,time,math
from PIL import Image,ImageDraw
out=Path("sketchfab-188-source-qa");out.mkdir(exist_ok=True)
input_data=json.loads(Path("catalog/sketchfab_multilingual_cc_188_candidates_20261106.json").read_text())["models"]
existing={x["uid"] for x in json.loads(Path("catalog/verified_drive_inventory_quality_142_20261106.json").read_text())["models"]}
ban=re.compile(r"photo booth|phone booth|telephone booth|ticket booth|dj booth|toll booth|security booth|sound booth|minecraft|roblox|vrchat|metaverse|avatar|arcade|game|showcase single|bookstand|nightstand|laptop stand|logo sign|reception counter|standalone sign|curtain pole|lighting downspot|counter pillar|food truck|farm exhibition painting|model vessel|amphora",re.I)
strong=re.compile(r"exhibit|trade.?show|expo|booth|stand|fuar|messe|feria|fiera|estande|pavilion|store|event|brand",re.I)
cands=[row for row in input_data if row["uid"] not in existing and not ban.search(row["title"] or "") and strong.search((row["title"] or "")+" "+(row["description"] or ""))]
print("INPUT",len(input_data),"FRESH_AFTER_FILTER",len(cands),flush=True)
def fetch(r):
 uid=r["uid"];base="https://mirror.traines.eu/sketchfab-backup/"+uid[:2]+"/"+uid
 data=dict(r);s=requests.Session();s.headers.update({"User-Agent":"ExpoVault-selective-licensed-3D-model-inventory/1.0"})
 for key,suffix in [("gltf",".zip"),("creator_source",".source.zip")]:
  try:
   h=s.head(base+suffix,timeout=(8,24),allow_redirects=True)
   data[key+"_status"]=h.status_code
   data[key+"_bytes"]=int(h.headers.get("content-length") or 0)
  except Exception as e:data[key+"_error"]=str(e)[:120]
 img=None
 if data.get("gltf_status")==200 and data.get("creator_source_status")==200:
  try:
   d=s.get(base+".thumb.jpeg",timeout=(8,22));d.raise_for_status()
   img=Image.open(BytesIO(d.content)).convert("RGB")
  except Exception as e:data["preview_error"]=str(e)[:110]
 return data,img
with ThreadPoolExecutor(max_workers=5) as pool:result=list(pool.map(fetch,cands))
available=[x for x in result if x[0].get("gltf_status")==200 and x[0].get("creator_source_status")==200 and x[0].get("gltf_bytes",0)>15000]
available.sort(key=lambda x:(0 if re.search(r"exhibition|expo|trade.?show|messestand|messebau|fuar|feria",x[0]["title"],re.I) else 1,-x[0].get("gltf_bytes",0)))
all_data={"checked":len(cands),"source_files_verified":len(available),"assets":[r for r,img in available],
          "errors_or_missing":[r for r,img in result if r.get("gltf_status")!=200 or r.get("creator_source_status")!=200]}
(out/"eligible_source_models.json").write_text(json.dumps(all_data,ensure_ascii=False,indent=2))
print("ARCHIVE_SOURCE_AVAILABLE",len(available),flush=True)
for i,(r,im) in enumerate(available):
 print("AVAILABLE",i+1,r["uid"],r["license"],r["title"][:60],r.get("gltf_bytes",0)//1048576,r.get("creator_source_bytes",0)//1048576,flush=True)
W,H=330,240
for page in range((len(available)+19)//20):
 subset=available[page*20:page*20+20]
 board=Image.new("RGB",(W*4,H*5),(245,245,245));draw=ImageDraw.Draw(board)
 for i,(r,im) in enumerate(subset):
  x=i%4*W;y=i//4*H
  if im:
   im.thumbnail((W-6,165));board.paste(im,(x+(W-im.width)//2,y+(165-im.height)//2))
  draw.text((x+4,y+171),str(page*20+i+1)+". "+r["title"][:44],fill="black")
  draw.text((x+4,y+188),r["uid"],fill="black")
  draw.text((x+4,y+209),f"3D {r.get('gltf_bytes',0)//1048576}MB / Native {r.get('creator_source_bytes',0)//1048576}MB",fill="black")
 board.save(out/f"qa_sheet_{page+1:02d}.jpg",quality=82)
