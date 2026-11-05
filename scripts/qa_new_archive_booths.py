import zipfile,json,io,pathlib,re,requests,concurrent.futures as cf
from PIL import Image,ImageDraw
out=pathlib.Path("wave09-booth-quality");out.mkdir(exist_ok=True)
known={x["uid"] for x in json.loads(pathlib.Path("catalog/verified_drive_inventory_quality_136_20261105.json").read_text())["models"]}
with zipfile.ZipFile("candidate-input/metadata.zip") as z:
    assert z.testzip() is None
    all_source=json.loads(z.read("new_licensed_booth_candidates.json"))["candidates"]
ban=re.compile(r"guard booth|telephone|phone booth|photo booth|blackpink|lightstick|cardboard closet|kiosk kit|stand (test)|booth sign|DJ booth",re.I)
new=[x for x in all_source if x["uid"] not in known and not ban.search(x.get("title") or "")]
print("CC_LIBRARY_34","KNOWN",len(known),"FRESH",len(new),flush=True)
s=requests.Session();s.headers["User-Agent"]="ExpoVault-CC-exhibition-booth-original-visual-curation/1.0"
def read(x):
    u=x["uid"];ret={k:x.get(k) for k in ["uid","title","creator","license","original_gltf_zip","creator_source_zip","preview_url"]}
    for k,url in [("original",x["original_gltf_zip"]),("native",x["creator_source_zip"])]:
        try:
            r=s.head(url,timeout=(7,16))
            ret[k+"_status"]=r.status_code
            ret[k+"_bytes"]=int(r.headers.get("content-length") or 0)
        except Exception as e:ret[k+"_error"]=str(e)[:130]
    im=None
    try:
        r=s.get(x["preview_url"],timeout=(8,17));r.raise_for_status()
        im=Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:ret["image_error"]=str(e)[:130]
    return ret,im
with cf.ThreadPoolExecutor(max_workers=4) as ex:entries=list(ex.map(read,new))
valid=[(r,img) for r,img in entries if r.get("original_status")==200 and r.get("native_status")==200]
(out/"valid_candidates.json").write_text(json.dumps({"fresh_candidates":len(new),"original_downloadable":len(valid),"items":[x for x,i in valid]},ensure_ascii=False,indent=2))
W,H=342,255
for page in range((len(valid)+19)//20):
    subset=valid[page*20:page*20+20]
    board=Image.new("RGB",(5*W,4*H),"white");dr=ImageDraw.Draw(board)
    for i,(r,im) in enumerate(subset):
        x=i%5*W;y=i//5*H
        if im is not None:
            im.thumbnail((W-5,191));board.paste(im,(x+(W-im.width)//2,y+(191-im.height)//2))
        dr.text((x+4,y+195),str(page*20+i+1)+". "+str(r["title"])[:42],fill="black")
        dr.text((x+4,y+216),r["uid"],fill="black")
        dr.text((x+4,y+233),f"GLTF {r.get('original_bytes',0)//1048576}MB NATIVE {r.get('native_bytes',0)//1048576}MB",fill="black")
    board.save(out/f"contact_{page+1:02d}.jpg",quality=83)
print("LICENSED_UNCOLLECTED_NEW",len(valid),flush=True)
for i,(r,_) in enumerate(valid):print("VISUAL_CANDIDATE",i+1,r["uid"],r["title"],r.get("original_bytes",0)//1048576,r.get("native_bytes",0)//1048576,flush=True)
