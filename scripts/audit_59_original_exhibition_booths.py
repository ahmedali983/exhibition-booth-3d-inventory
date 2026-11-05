from pathlib import Path
import requests,json,concurrent.futures as cf,re
from PIL import Image,ImageDraw
from io import BytesIO
ROOT=Path.cwd()
data=json.loads((ROOT/"catalog/new_real_booth_discovery_20261105.json").read_text(encoding="utf8"))
rows=[x for x in data["entries"] if x["looks_like_complete_booth"] and not x["in_source_archive"]]
seen=set()
excluded=re.compile(r"photo scan|just (?:a )?counter|logo|pantry|exhibition-booth-3d-wall|screen-display|closet|booth-rotatable|top-sign|reception table|floor|industrial exhibition stand photo|please do not use|no debe ser utilizado",re.I)
rows=[x for x in rows if not excluded.search(x["title"]+" "+x["description"])]
rows.sort(key=lambda x:-int(x.get("views") or 0))
rows=[x for x in rows if not(x["uid"] in seen or seen.add(x["uid"]))]
BASE="https://mirror.traines.eu/sketchfab-backup/"
s=requests.Session();s.headers["User-Agent"]="ExpoVault-original-licensed-stand-inventory/1.0"
def audit(x):
 uid=x["uid"]
 base=BASE+uid[:2]+"/"+uid
 record={k:x.get(k) for k in ["uid","title","source_url","views","likes","description"]}
 record["archive_url"]=base+".zip"
 record["source_archive_url"]=base+".source.zip"
 record["thumbnail_url"]=base+".thumb.jpeg"
 for ext,label in [(".zip","original_gltf"),(".source.zip","original_source")]:
  try:
   r=s.head(base+ext,timeout=(6,18),allow_redirects=True)
   record[label]={"http_status":r.status_code,"bytes":int(r.headers.get("content-length") or 0)}
  except Exception as e:record[label]={"error":str(e)[:110]}
 return record
with cf.ThreadPoolExecutor(max_workers=4) as pool:checked=list(pool.map(audit,rows))
valid=[r for r in checked if r["original_gltf"].get("http_status")==200 and r["original_gltf"].get("bytes",0)>10000]
valid.sort(key=lambda x:(-int(x["views"] or 0),x["uid"]))
out=ROOT/"new-mirror-discovery";out.mkdir(exist_ok=True)
(out/"source_presence_audit.json").write_text(json.dumps({"checked":len(checked),"found_source_zip":len(valid),"valid":valid,"all":checked},ensure_ascii=False,indent=2),encoding="utf8")
print("CENSUS",len(checked),"EXISTING_LICENSE_ARCHIVE",len(valid),flush=True)
for z in valid:print("OPEN_ZIP",z["uid"],z["original_gltf"].get("bytes",0)//1000000,z["original_source"].get("bytes",0)//1000000,z["title"][:60],flush=True)
# Fetch only small thumbnails (not model files) for human visual selection
selected=valid[:28]
W,H=292,235
board=Image.new("RGB",(4*W,((len(selected)+3)//4)*H),(243,246,248))
draw=ImageDraw.Draw(board)
for i,r in enumerate(selected):
 x=i%4*W;y=i//4*H
 try:
  res=s.get(r["thumbnail_url"],timeout=(6,20));res.raise_for_status()
  im=Image.open(BytesIO(res.content)).convert("RGB");im.thumbnail((W-10,H-62))
  board.paste(im,(x+(W-im.width)//2,y+(H-62-im.height)//2))
 except Exception as e:print("THUMB_ERROR",r["uid"],str(e)[:100],flush=True)
 draw.text((x+5,y+H-49),str(i+1)+". "+str(r["title"])[:37],fill=(30,30,45))
 draw.text((x+5,y+H-28),"glTF: "+str(r["original_gltf"]["bytes"]//1000000)+"MB; source: "+str(r["original_source"].get("bytes",0)//1000000)+"MB",fill=(80,90,105))
 draw.text((x+5,y+H-12),str(r["uid"]),fill=(105,105,115))
board.save(out/"booth_previews.jpg",quality=84)
