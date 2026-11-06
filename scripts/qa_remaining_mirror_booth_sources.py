#!/usr/bin/env python3
"""Visually curate genuine, openly licensed booth originals discovered across archive directory groups."""
import json,re,pathlib,concurrent.futures as cf,requests
from io import BytesIO
from PIL import Image,ImageDraw
root=pathlib.Path("mirror-fresh-candidates")
root.mkdir(exist_ok=True)
existing={x["uid"] for x in json.loads(pathlib.Path("catalog/verified_drive_inventory_quality_142_20261106.json").read_text())["models"]}
results=[]
for folder in sorted(pathlib.Path("input").iterdir()):
 p=folder/"new_licensed_booth_candidates.json"
 if p.exists():
  data=json.loads(p.read_text(encoding="utf8"))
  print("INPUT",folder.name,"LICENSED",len(data["candidates"]),flush=True)
  results.extend(data["candidates"])
skip=re.compile(r"guard.?booth|bus.?stand|phone.?booth|photo.?booth|voting.?booth|dj.?booth|ticket.?booth|food.?stall|lightstick|closet|chair|counter.?only|single.?stand|flag.?stand|banner.?stand|toy|minecraft|roblox|display.?wall|nightstand|shelf|house|bedroom|classroom|gas.?station",re.I)
prefer=re.compile(r"exhibition|expo|fair|tradeshow|trade.show|exposition|fuar|messe|booth|pavilion|stall|messen|fiera|feria|messen|estande|выстав",re.I)
seen=set();candidates=[]
for item in results:
 uid=item["uid"]
 if uid in existing or uid in seen:continue
 seen.add(uid)
 name=str(item.get("title") or item.get("slug") or "")
 if skip.search(name):continue
 if not prefer.search(name) and not re.search(r"stand",name,re.I):continue
 candidates.append(item)
print("FRESH_BOOTH_TITLES",len(candidates),"KNOWN_UIDS",len(existing),flush=True)
def check(item):
 uid=item["uid"]
 root="https://mirror.traines.eu/sketchfab-backup/"+uid[:2]+"/"+uid
 obj={**item}
 for ext,key in [(".zip","glTF_original"),(".source.zip","creator_native")]:
  try:
   response=requests.head(root+ext,timeout=(10,20),allow_redirects=True,headers={"User-Agent":"ExpoVault-original-3D-booth-validation/1.0"})
   obj[key+"_status"]=response.status_code
   obj[key+"_bytes"]=int(response.headers.get("content-length") or 0)
  except Exception as e:obj[key+"_error"]=str(e)[:120]
 im=None
 try:
  r=requests.get(root+".thumb.jpeg",timeout=(10,25));r.raise_for_status()
  im=Image.open(BytesIO(r.content)).convert("RGB")
 except Exception as e:obj["preview_error"]=str(e)[:120]
 return obj,im
with cf.ThreadPoolExecutor(max_workers=4) as pool:items=list(pool.map(check,candidates))
ready=[x for x in items if x[0].get("glTF_original_status")==200 and x[0].get("glTF_original_bytes",0)>10000 and x[0].get("creator_native_status")==200]
ready.sort(key=lambda x:(0 if re.search(r"exhibition|trade.?show|expo|messestand|messebau|fuar|feria",str(x[0].get("title") or ""),re.I) else 1,0 if x[1] is not None else 1,-x[0].get("glTF_original_bytes",0)))
manifest={"known_existing_UIDs":len(existing),"total_license_checked":len(results),"new_full_booth_title_candidates":len(candidates),"archived_originals_available":len(ready),"candidates":[x for x,im in ready]}
(root/"READY_FOR_VISUAL_QA.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
print("READY_FOR_VISUAL_QA",len(ready),flush=True)
for i,(item,im) in enumerate(ready):
 print("CANDIDATE",i+1,item["uid"],item.get("license"),str(item.get("title"))[:65],flush=True)
W,H=335,250
for p in range((len(ready)+19)//20):
 subset=ready[p*20:p*20+20]
 board=Image.new("RGB",(W*4,H*5),"white");draw=ImageDraw.Draw(board)
 for i,(row,img) in enumerate(subset):
  x=(i%4)*W;y=(i//4)*H
  if img:
   img.thumbnail((W-8,175));board.paste(img,(x+(W-img.width)//2,y+(175-img.height)//2))
  draw.text((x+4,y+180),str(p*20+i+1)+". "+str(row.get("title") or row["uid"])[:46],fill="black")
  draw.text((x+4,y+200),row["uid"],fill="black")
  draw.text((x+4,y+220),"Original "+str(row.get("glTF_original_bytes",0)//1048576)+"MB / Source "+str(row.get("creator_native_bytes",0)//1048576)+"MB",fill="black")
 board.save(root/f"contact_{p+1:02d}.jpg",quality=85)
