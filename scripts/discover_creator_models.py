#!/usr/bin/env python3
"""Index third-party booth MODEL METADATA from the public Sketchfab search API."""
import argparse,json,pathlib,time,re,datetime as dt,urllib.request,urllib.parse,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
TERMS=("exhibition booth","exhibition stand","expo booth","expo stand","trade show booth","trade show stand",
"exhibition stall","tradeshow stand","exhibit display","exhibit booth","trade fair booth","expo pavilion",
"event booth","exhibition kiosk","exhibition structure","retail kiosk","mall booth","event display",
"portable booth","shell scheme stand","island booth","peninsula booth","corner booth","corporate booth",
"brand activation booth","product launch booth","exhibition architecture","exhibition hall","exhibition interior",
"pharma exhibition booth","medical exhibition stand","fashion exhibition booth","food trade show",
"automotive exhibition booth","construction exhibition booth","museum exhibition stand","trade booth",
"display stand","modular exhibition stand","booth design","stand design","3D expo","event exhibit",
"event booth design","show booth","exhibition counter","truss exhibition","exhibition furniture",
"commercial display booth","exhibition reception desk","event stand","convention exhibit","exhibition pavilion")
REGEX=re.compile(r"\b(booth|exhib|expo|trade.?show|fair|kiosk|stall|pavilion|truss|display.?stand|stand.?design|event stand|brand activation)\b",re.I)
def main():
 p=argparse.ArgumentParser();p.add_argument("--pages",type=int,default=6);p.add_argument("--delay",type=float,default=.1);a=p.parse_args()
 original=json.loads((ROOT/"catalog"/"sketchfab_index.json").read_text(encoding="utf-8"))["items"]
 known={x["id"] for x in original};rows={}
 for i,term in enumerate(TERMS,1):
  url="https://api.sketchfab.com/v3/search?"+urllib.parse.urlencode({"type":"models","q":term,"count":24})
  count=0
  for page in range(a.pages):
   try:
    req=urllib.request.Request(url,headers={"User-Agent":"ExpoVaultCatalog/2.0"})
    with urllib.request.urlopen(req,timeout=16) as f:d=json.load(f)
   except Exception as e:
    print("QUERY_STOP",term,type(e).__name__,flush=True);break
   results=d.get("results") or []
   if not results:break
   for v in results:
    count+=1;uid=v.get("uid");title=(v.get("name") or "").strip()
    if not uid or not REGEX.search(title) or "SKFB-"+uid in known:continue
    user=v.get("user") or {};lic=v.get("license") or {}
    lic=lic.get("label") or lic.get("slug") or "Unspecified" if isinstance(lic,dict) else str(lic)
    imgs=(v.get("thumbnails") or {}).get("images") or [];thumbnail=next((im.get("url") for im in reversed(imgs) if im.get("url")),None)
    allowed=bool(v.get("isDownloadable"))
    rows[uid]={"id":"SKFB-"+uid,"site":"Sketchfab","url":"https://sketchfab.com/models/"+uid,"title":title[:170],
      "author":user.get("username") or "Unknown","thumbnail":thumbnail,"license":lic,
      "format":"3D model; creator-dependent file format","status":"Creator download listing" if allowed else "Preview only / no public model download",
      "notes":"Original creator model; follow platform's licence and permissions",
      "is_downloadable":allowed,"view_count":v.get("viewCount") or 0,"origin":"metadata-only"}
   url=d.get("next")
   if not isinstance(url,str) or not url.startswith("https://api.sketchfab.com/"):break
   time.sleep(max(0,a.delay))
  print(f"{i}/{len(TERMS)} {term}: {count} scanned / {len(rows)} new unique",flush=True)
 target=ROOT/"catalog"/"creator_discovery.json"
 items=sorted(rows.values(),key=lambda x:-x["view_count"])
 target.write_text(json.dumps({"source":"Sketchfab public metadata","count":len(items),"generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"items":items},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
 print("DONE",len(items),"third-party model metadata records",flush=True)
if __name__=="__main__":main()
