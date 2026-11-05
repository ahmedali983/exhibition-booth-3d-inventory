from pathlib import Path
import tempfile,requests,pandas as pd,re,collections,json
root=Path(tempfile.gettempdir())/"expovault_build_20261104"
cache=Path(tempfile.gettempdir())/"expovault_prosceneverse_metadata.parquet"
if not cache.exists():
 url="https://huggingface.co/datasets/Stable-X/ProSceneverse/resolve/main/metadata.parquet"
 r=requests.get(url,timeout=80);r.raise_for_status()
 cache.write_bytes(r.content)
print("FILE",cache,len(cache.read_bytes()),flush=True)
df=pd.read_parquet(cache)
print("ROWS",len(df),"COLUMNS",list(df.columns),flush=True)
valid=df[df["license_slug"].isin(["by","cc0"])].copy()
print("OPEN_CC_BY_OR_CC0",len(valid),flush=True)
regex_exact=r"\b(?:exhibition\s+(?:booth|stand|stall)|expo\s+(?:booth|stand)|trade\s*show\s+(?:booth|stand)|tradeshow\s+(?:booth|stand)|exhibit\s+(?:booth|stand)|(?:booth|stand)\s+design|fair\s+stand|showroom\s+(?:booth|stand))\b"
regex_broad=r"\b(?:exhibition|expo|exhibit|trade[\s-]?show|fairground|pavilion|kiosk|stall|showroom|museum|display\s+stand|stand\s+design|retail\s+store|gallery|booth)\b"
def text_column(part):
 return valid[part].fillna("").astype(str)
name=text_column("name")
desc=text_column("description")
caption=text_column("caption")
mask_exact=name.str.contains(regex_exact,case=False,regex=True)|desc.str.contains(regex_exact,case=False,regex=True)
mask_scene=(name+" "+desc+" "+caption).str.contains(regex_broad,case=False,regex=True)
print("EXACT_BOOTH",int(mask_exact.sum()),"RELEVANT_WIDE",int(mask_scene.sum()),flush=True)
print("EXACT_BY_CATEGORY",valid[mask_exact]["category"].value_counts().to_dict(),flush=True)
print("WIDE_BY_CATEGORY",valid[mask_scene]["category"].value_counts().to_dict(),flush=True)
print("SAMPLES",[(str(x["name"])[:76],str(x["license_slug"]),str(x["category"])) for _,x in valid[mask_exact].head(22).iterrows()],flush=True)
# Scoring is retrieval confidence only, not confirmation of full-booth geometry.
out=[]
for _,row in valid[mask_scene].iterrows():
 title=str(row["name"] or "")
 caption=str(row["caption"] or "")
 combined=" ".join((title,str(row["description"]),caption)).lower()
 score=0
 if re.search(regex_exact,title,re.I):score+=120
 elif re.search(regex_exact,combined,re.I):score+=85
 if re.search(r"\b(?:exhibition\s+(?:hall|design|display|furniture)|expo\b|showroom|pavilion|trade\s*show|exhibit\b)",title,re.I):score+=40
 if re.search(r"\b(?:booth|stand|kiosk|gallery|retail\s+store)\b",title,re.I):score+=18
 if str(row["category"])=="CAD_ARCHITECTURE":score+=12
 if re.search(r"\b(?:game|fantasy|medieval|sci-fi|minecraft|lowpoly|photogrammetry|scan)\b",title,re.I):score-=50
 out.append({
  "uid":str(row["scene_id"]),"title":title[:240],"category":str(row["category"]),
  "author":str(row["author_username"] or ""),"license":str(row["license_slug"]),
  "archive_format":"prosceneverse_15gb_tar_shard","source_url":str(row["source_url"] or ""),
  "shard_member":str(row["file_name"]),"face_count":int(row["face_count"] or 0),
  "score":score,"availability":"LICENSE_METADATA_ONLY_NOT_HOSTED",
  "preview":str(row["thumbnail"] or ""),
 })
out.sort(key=lambda a:(-a["score"],a["title"]))
summary={"dataset":"Stable-X/ProSceneverse","total_rows":len(df),"cc_by_or_cc0":len(valid),"highly_specific_exhibition_booth_title_or_description":int(mask_exact.sum()),"broad_exhibition_related_caption_or_metadata":int(mask_scene.sum()),"note":"These are metadata candidates, not downloaded assets. Scenes are stored in ~15 GB tar shards.","top_candidates":out[:200]}
(root/"catalog"/"prosceneverse_booth_census_20261105.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("TOP20",[(x["score"],x["title"][:70]) for x in out[:20]],flush=True)
print("RESEARCH_FILE",root/"catalog"/"prosceneverse_booth_census_20261105.json",flush=True)
