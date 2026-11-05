"""Public directory metadata-only discovery for additional creator-authored trade show booth assets.
Do not copy bulk 3D archive. Stop after bounded 48 metadata directories.
"""
import requests,re,json,concurrent.futures as cf,random,pathlib,html
OUT=pathlib.Path("mirror-title-discovery");OUT.mkdir(exist_ok=True)
BASE="https://mirror.traines.eu/sketchfab-backup/"
# 48 distinct hex directory prefixes beyond the already examined 16 original shards.
SHARDS=[f"{i:02x}" for i in range(256) if i%16 in (3,7,11)][:48]
PAT=re.compile(r"(?:(?:exhibition|trade[-_. ]?show|trade[-_. ]?fair|expo|exposit|convention|fair|messe|fuar|feria|fiera|estande)[-_. ]+(?:booth|stand|stall|design|pavilion|kiosk)|(?:booth|stand)[-_. ]+(?:exhibition|expo|trade|fair|feria|messen)|messestand|messebau|fuar[-_. ]?stand|booth[-_. ]?(?:design|3d|[0-9]{1,2}x[0-9]{1,2})|stand[-_. ]?(?:design|3d|exposit|fierist)|выстав|展位|展台)",re.I)
SKIP=re.compile(r"phone[-_. ]?booth|photo[-_. ]?booth|ticket[-_. ]?booth|dj[-_. ]?booth|voting[-_. ]?booth|nightstand|minecraft|roblox|game|fortnite|food[-_. ]?stall|counter[-_. ]?only|toll[-_. ]?booth|booth[-_. ]?sign",re.I)
def check(shard):
 try:
  u=BASE+shard+"/"
  r=requests.get(u,timeout=(10,40),headers={"User-Agent":"ExpoVault-selective-CC-booth-metadata-census/1.0"});r.raise_for_status()
  names=[html.unescape(x) for x in re.findall(r'href="([^"]+)"',r.text)]
  matches=[]
  for name in names:
   if ".m." not in name or not name.endswith(".json"):continue
   uid=name[:32]
   if not re.fullmatch(r"[a-f0-9]{32}",uid):continue
   slug=name[35:-5]
   if not PAT.search(slug) or SKIP.search(slug):continue
   matches.append({"uid":uid,"slug":slug,"mirror_metadata_url":u+name,"original_gltf_zip":u+uid+".zip","creator_source_zip":u+uid+".source.zip","preview_url":u+uid+".thumb.jpeg"})
  print("DIRECTORY",shard,len(names),"TITLE_MATCHES",len(matches),flush=True)
  return {"shard":shard,"listing_count":len(names),"matches":matches}
 except Exception as e:
  print("DIRECTORY_ERROR",shard,str(e)[:100],flush=True)
  return {"shard":shard,"error":str(e)[:200],"matches":[]}
with cf.ThreadPoolExecutor(max_workers=4) as pool:res=list(pool.map(check,SHARDS))
records=[v for r in res for v in r["matches"]]
unique=list({x["uid"]:x for x in records}.values())
print("DIRECTORY_SCAN_DONE",len(SHARDS),"MATCHES",len(records),"UIDS",len(unique),flush=True)
def validate(x):
 try:
  res=requests.get(x["mirror_metadata_url"],timeout=17)
  res.raise_for_status();d=res.json()
  user=(d.get("user") or {}).get("username")
  lic=d.get("license") or {}
  slug=lic.get("slug","") if isinstance(lic,dict) else ""
  label=lic.get("label","") if isinstance(lic,dict) else str(lic)
  if not slug and "attribution" in label.lower():slug="by"
  if not user or slug not in ("by","by-sa","cc0"):
   return {**x,"eligible":False,"creator":user,"license":slug}
  desc=str(d.get("description") or "")
  if re.search(r"without authorization|no debe ser utilizado|do not use|not for reupload|no redistribution",desc,re.I):
   return {**x,"eligible":False,"reason":"creator permission conflict"}
  return {**x,"eligible":True,"creator":user,"license":slug,"title":d.get("name"),"description":desc[:180]}
 except Exception as e:return {**x,"eligible":False,"error":str(e)[:120]}
with cf.ThreadPoolExecutor(max_workers=3) as pool:checked=list(pool.map(validate,unique))
valid=[x for x in checked if x.get("eligible")]
report={"method":"bounded 48-directory metadata-only census; no GLB payloads downloaded","shards":res,"candidates":valid,"total_candidate_uids":len(unique),"valid_cc_originals":len(valid),"errors":[x for x in checked if not x.get("eligible")]}
(OUT/"new_licensed_booth_candidates.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("LICENSED_CANDIDATES",len(valid),flush=True)
for x in valid:print("LICENSED",x["uid"],x["license"],str(x.get("title"))[:55],flush=True)
