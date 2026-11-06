#!/usr/bin/env python3
"""World-wide source-authorized booth metadata discovery and public archive preflight.

Searches official Sketchfab public catalog, retaining per-model Creative Commons evidence.
Does not rip a viewer or download view-only/nonredistributable assets.
No result is counted as a complete professional booth without 3D manual QA.
"""
import concurrent.futures, json, os, re, sys, time
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GROUPS = {
"EN_CORE": [
"exhibition stand","exhibition booth","exhibition stall","expo stand","trade show booth",
"trade show stand","custom exhibition stand","exhibition stand design","exhibition booth 3d",
"exhibition pavilion","corporate exhibition booth","event booth design","exhibition booth architecture"],
"EN_SPECIFIC": [
"3m x 3m exhibition booth","6x6 exhibition stand","20x30 trade show booth","island exhibition booth",
"double deck exhibition stand","two story exhibition stand","modular exhibition stand",
"corner exhibition booth","exhibition stand rendering","expo stand design","conference booth 3d",
"retail expo booth","brand exhibition booth","booth show floor"],
"EUROPE_WEST": [
"stand salon professionnel","stand exposition","stand de foire","kiosque exposition",
"stand événementiel","stand fieristico","stand fiera","stand espositivo",
"allestimento fieristico","esposizione fieristica","beursstand","tentoonstellingsstand"],
"EUROPE_CENTRAL": [
"Messestand","Messebau","Ausstellungsstand","Messestand Design","Messe Stand",
"Messestand 3D","stoisko targowe","stoisko wystawowe","výstavní stánek",
"výstavný stánok","exhibition stand germany","pabellon ferial"],
"IBERIA_LATAM": [
"stand de feria","stand de exposición","diseño de stand","stand ferial",
"stand para exposicion","pabellón exposición","estande feira","estande exposição",
"design estande","stand de exposição","estande promocional","stand de exposiciones"],
"RUS_CIS": [
"выставочный стенд","дизайн выставочного стенда","выставочный павильон",
"экспозиционный стенд","стенд выставки","выставочный стенд 3d",
"виставковий стенд","дизайн стенда","павильон выставки","торговый павильон"],
"ARAB_TURKISH": [
"جناح معرض","بوث معرض","تصميم جناح معرض","ستاند معرض","معرض تجاري","ديكور معرض",
"fuar standı","fuar stand tasarımı","sergi standı","fuar stand","sergi stand tasarımı"],
"ASIA_EAST": [
"展会展台","展览展位","展台设计","展览展台","展会设计",
"展示会ブース","展示ブース","展示会 スタンド","展示会ブースデザイン",
"전시 부스","전시회 부스","전시부스 디자인"],
"ASIA_SOUTH": [
"booth pameran","stand pameran","gian hàng triển lãm","thiết kế gian hàng triển lãm",
"บูธแสดงสินค้า","บูธนิทรรศการ","प्रदर्शनी स्टॉल","प्रदर्शनी बूथ",
"غرفه نمایشگاهی","طراحی غرفه نمایشگاهی","exhibition booth india","exhibition stand dubai"],
"EN_EXPANDED": [
"trade fair pavilion","exhibition shell scheme","trade show kiosk stand",
"commercial expo booth","exhibitor stand","trade fair booth design",
"expo exhibition stand interior","event stand 3d model","expo booth architecture",
"convention exhibitor pavilion","exhibition stall design","exhibit space design"]
}
API = "https://api.sketchfab.com/v3/search"
UA = {"User-Agent": "ExpoVault-licensed-stand-catalog-research/2.0 (rights-first, metadata only)"}
BAD = re.compile(r"photo.?booth|dj.?booth|phone.?booth|voting.?booth|toilet|guard.?booth|bus.?stand|book.?stand|coat.?stand|cup.?stand|music.?stand|nightstand|weapon.?stand|vrchat|metaverse|minecraft|roblox|avatar|gas.?station|painting|poster.?only|single.?counter|shower|parking|football.?stand|car.?stand|camera.?stand|model.?figure|stand.?up.?comic", re.I)
GOOD = re.compile(r"exhibi|exposi|expo|trade.?show|trade.?fair|convention|booth|pavilion|stall|messe|fiera|feria|fuar|estande|выстав|стенд|展会|展览|展台|展示会|展示ブース|전시|معرض|جناح|غرفه|targow|výstav|pameran|triển lãm|นิทรรศการ|प्रदर्शनी", re.I)
IMPORTANT = re.compile(r"exhibi.{0,16}(booth|stand|stall)|trade.{0,10}(booth|stand)|expo.{0,12}(booth|stand|pavilion)|messestand|messebau|stand.{0,10}(fiera|feria)|выставочный стенд|展台设计|جناح معرض|fuar stand|stand de feria|estande feira", re.I)
ARCHIVE = "https://mirror.traines.eu/sketchfab-backup/"
PART = sys.argv[1] if len(sys.argv)>1 else "EN_CORE"
if PART not in GROUPS: raise SystemExit(f"Unknown group {PART}")
out = Path("worldwide-booths") / PART
out.mkdir(parents=True, exist_ok=True)
existing = set(json.loads(Path("catalog/expovault_known_uids_204_20261106.json").read_text(encoding="utf-8"))["uids"])
def session():
    s=requests.Session()
    s.headers.update(UA)
    retry=Retry(total=3,backoff_factor=0.8,status_forcelist=(429,500,502,503,504),respect_retry_after_header=True)
    s.mount("https://",HTTPAdapter(max_retries=retry))
    return s
def license_name(d):
    lic=d.get("license") or {}
    label=str(lic.get("label") if isinstance(lic,dict) else lic).lower()
    if "noncommercial" in label or "no derivatives" in label or "nc" in label.split() or "nd" in label.split(): return None
    if "cc0" in label or "public domain" in label: return "CC0"
    if "sharealike" in label or "share-alike" in label: return "CC-BY-SA"
    if "attribution" in label: return "CC-BY"
    return None
def query_one(q):
    s=session(); url=API;params={"type":"models","q":q,"downloadable":"true","count":24}
    data=[];errs=[];n=0
    while url and n<7:
        try:
            r=s.get(url,params=params,timeout=(10,35)); r.raise_for_status()
            v=r.json(); arr=v.get("results") or []
            data.extend(arr);url=v.get("next");params=None;n+=1
            if not arr: break
            time.sleep(0.32)
        except Exception as ex: errs.append(f"{q}: page{n+1}: {str(ex)[:180]}");break
    print("QUERY",q,"pages",n,"returned",len(data),"errors",len(errs),flush=True)
    return q,data,errs
rows={};errors=[];queries=GROUPS[PART]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for q,data,err in pool.map(query_one, queries):
        errors.extend(err)
        for d in data:
            uid=d.get("uid") or ""
            title=d.get("name") or ""
            tags=[x.get("name") or x.get("slug") or "" for x in d.get("tags") or [] if isinstance(x,dict)]
            description=re.sub(r"<[^>]+>"," ",str(d.get("description") or ""))[:1500]
            joined=(title+" "+" ".join(tags)+" "+description)
            if not re.fullmatch("[0-9a-f]{32}",uid) or uid in existing or BAD.search(title) or not GOOD.search(joined):continue
            if not d.get("isDownloadable") or d.get("isAgeRestricted"):continue
            lic=license_name(d)
            if lic is None: continue
            # Low relevance: retained in metadata but never promoted without checking actual geometry.
            exact=bool(IMPORTANT.search(title))
            score=100 if exact else 30
            if any(re.search(p,title,re.I) for p in ["stand","booth","exhibition","exhibit","expo","messe","fuar","feria","fiera","стенд","展台","展示","معرض","estande","pameran"]):score+=15
            score+=min(30, int(d.get("likeCount") or 0)//8)
            faces=int(d.get("faceCount") or 0)
            if 1500<faces<5000000:score+=10
            record=rows.setdefault(uid,{"uid":uid,"title":title,"description":description[:450],"tags":tags[:30],"license_historical":lic,
                "source_url":d.get("viewerUrl") or "https://sketchfab.com/models/"+uid,
                "creator":(d.get("user") or {}).get("username") or "",
                "faces":faces,"likes":int(d.get("likeCount") or 0),"views":int(d.get("viewCount") or 0),
                "score":score,"exact_title_candidate":exact,"queries":[],"group":PART,"stage":"METADATA_DISCOVERY_ONLY"})
            if q not in record["queries"]:record["queries"].append(q)
            record["score"]=max(record["score"],score)
ordered=sorted(rows.values(),key=lambda x:(-x["score"],-x["likes"],-x["faces"]))
print("DISCOVERED",PART,len(ordered),"HIGH_TITLE",sum(bool(x["exact_title_candidate"]) for x in ordered),"BASE204_EXCLUDED",len(existing),flush=True)
def archive_check(item):
    s=session(); uid=item["uid"]; root=ARCHIVE+uid[:2]+"/"+uid
    row=item.copy()
    for suffix,key in ((".zip","glTF"),(".source.zip","native")):
        try:
            h=s.head(root+suffix,timeout=(8,22),allow_redirects=True)
            row[key+"_http"]=h.status_code
            row[key+"_bytes"]=int(h.headers.get("Content-Length") or 0)
        except Exception as ex:row[key+"_error"]=str(ex)[:100]
    # These source mirrors are historical, do not imply a current license grant.
    row["archive_ready"]=row.get("glTF_http")==200 and row.get("glTF_bytes",0)>8000
    return row
limit=150
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
    ready=list(pool.map(archive_check,ordered[:limit]))
ready.sort(key=lambda x:(not x["archive_ready"],-x["score"],-x["likes"]))
result={"source":"official Sketchfab public search API + public historical object archive HEAD checks",
        "group":PART,"query_count":len(queries),"queries":queries,
        "catalog_results_distinct":len(ordered),"archive_checked":len(ready),
        "historical_public_glTF_ready":sum(x["archive_ready"] for x in ready),
        "stage":"SOURCE_DISCOVERY_ONLY","rights_rule":"Per-model current CC license and author conflicts must be checked before material download/rehosting. Never rip a view-only model.",
        "visual_rule":"Full professional exhibition booth and style uniqueness must be visually checked in 3D; props/modular pieces excluded from booth count",
        "errors":errors, "archive_preflight":ready,"metadata_only_unchecked":ordered[limit:]}
(out/"candidate_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("FINISHED",PART,"NEW_METADATA",len(ordered),"PUBLIC_ARCHIVE",result["historical_public_glTF_ready"],"ERRORS",len(errors),flush=True)
