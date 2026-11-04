#!/usr/bin/env python3
"""Index PUBLIC 3D metadata from Sketchfab without downloading or copying creator assets.
Sketchfab's official authenticated Download API is NOT bypassed.
Usage: python scripts/harvest_sketchfab.py --pages 5 --delay .15
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request
import urllib.error

ROOT=pathlib.Path(__file__).resolve().parents[1]
TERMS=[
 "exhibition booth", "exhibition stand", "exhibition stall", "expo booth",
 "expo stand", "trade show booth", "trade show stand", "tradeshow booth",
 "trade fair stand", "exhibition pavilion", "exhibition kiosk",
 "exhibition reception desk", "modular exhibition stand",
 "exhibition display stand", "event exhibition booth",
 "3d exhibition booth", "custom exhibition booth",
 "exhibition trade fair booth", "exhibition display booth",
 "event display booth", "exhibition truss", "exhibition furniture",
 "trade show display", "exhibit booth", "exhibition counter",
]
STRONG=re.compile(r"\b(exhibition|expo|trade.?show|tradeshow|trade.?fair|booth|stall|pavilion|kiosk|display.?stand|truss)\b",re.I)
API="https://api.sketchfab.com/v3/search?"+urllib.parse.urlencode({"type":"models","q":"exhibition booth","downloadable":"true","count":24})

def search_term(term,pages,delay):
    url="https://api.sketchfab.com/v3/search?"+urllib.parse.urlencode({"type":"models","q":term,"downloadable":"true","count":24})
    for page in range(pages):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ExpoVaultResearch/1.0 (model metadata, attribution)"})
            with urllib.request.urlopen(req,timeout=18) as rsp:data=json.load(rsp)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
            print("  API error",term,page,str(exc)[:130],flush=True)
            break
        results=data.get("results") or []
        if not results:break
        for model in results:yield model
        next_url=data.get("next")
        if not next_url or not next_url.startswith("https://api.sketchfab.com/"):
            break
        url=next_url
        time.sleep(max(delay,0))

def simplify(m):
    uid=m.get("uid")
    if not uid:return None
    title=(m.get("name") or "").strip()[:170]
    if not STRONG.search(title):
        return None
    user=m.get("user") or {}
    author=user.get("username") or user.get("displayName") or "unknown"
    license_obj=m.get("license")
    if isinstance(license_obj,dict):license_name=license_obj.get("label") or license_obj.get("slug") or "Unknown"
    else:license_name=str(license_obj or "Unknown")
    page=m.get("viewerUrl") or ("https://sketchfab.com/3d-models/"+uid)
    if not page.startswith("https://sketchfab.com/"):page="https://sketchfab.com/3d-models/"+uid
    images=(m.get("thumbnails") or {}).get("images") or []
    thumb=images[-1].get("url") if images else None
    return {"id":"SKFB-"+uid,"title":title,"site":"Sketchfab","url":page,
        "author":author,"author_url":"https://sketchfab.com/"+urllib.parse.quote(author),
        "license":license_name,"format":"glTF archive (login-gated)",
        "notes":"Downloadable 3D model on original platform; geometry and manufacturing suitability not validated",
        "status":"Download via official Sketchfab account; do not rehost without rights",
        "thumbnail":thumb,"published_at":m.get("publishedAt"),
        "view_count":m.get("viewCount",0),
        "is_downloadable":bool(m.get("isDownloadable")),
        "origin":"external-metadata-only"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--pages",type=int,default=4)
    ap.add_argument("--delay",type=float,default=.12);ap.add_argument("--max-terms",type=int,default=len(TERMS))
    a=ap.parse_args()
    rows={}
    for i,term in enumerate(TERMS[:a.max_terms],1):
        before=len(rows);seen=0
        for m in search_term(term,max(1,a.pages),a.delay):
            seen+=1
            val=simplify(m)
            if val and val["is_downloadable"]:
                rows[val["id"]]=val
        print(f"{i:02d}/{min(len(TERMS),a.max_terms)} {term}: scanned {seen}, total unique {len(rows)} (+{len(rows)-before})",flush=True)
    ordered=sorted(rows.values(),key=lambda x:(-int(x["view_count"] or 0),x["title"]))
    target=ROOT/"catalog"/"sketchfab_index.json";target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({"source":"Sketchfab public Data API v3","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "count":len(ordered),"access":"Public metadata only; model download requires Sketchfab authentication",
        "items":ordered},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("DONE",len(ordered),"unique metadata entries ->",target,flush=True)
if __name__=="__main__":main()
