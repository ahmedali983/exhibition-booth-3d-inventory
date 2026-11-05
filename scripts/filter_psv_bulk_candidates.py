import json, re, io, requests, pathlib
import pandas as pd
from huggingface_hub import hf_hub_url

DATASET="Stable-X/ProSceneverse"
out=pathlib.Path("psv-bulk-candidates");out.mkdir(exist_ok=True)
baseline=json.loads(pathlib.Path("catalog/bulk_import_existing_uids.json").read_text())["current_verified_drive_uids"]
known=set(baseline)
def get_df(name):
    response=requests.get(hf_hub_url(DATASET,name,repo_type="dataset"),timeout=90)
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))

meta=get_df("metadata.parquet")
index=get_df("shard_index.parquet")
index=index[index.path.str.endswith(".glb")].sort_values(["shard","path"])
index["tar_order"]=index.groupby("shard").cumcount()
data=meta.merge(index,left_on="file_name",right_on="path")
data=data[data.license_slug.isin(["by","by-sa","cc0"])]
data=data[~data.scene_id.isin(known)]
bad=re.compile(r"without authoriz|no debe ser utilizado|do not use|photo.?booth|telephone booth|toll booth|food stall|game asset|ticket booth|bus stop|banner stand|table stand|nightstand|shelf|shelving",re.I)
explicit=re.compile(r"exhibition.{0,20}(?:booth|stand|stall|pavilion)|trade.{0,8}(?:show|fair).{0,18}(?:booth|stand|stall)|expo.{0,15}(?:booth|stand|stall)|fuar.{0,8}stand|messestand|messebau|exhibit.{0,8}booth",re.I)
scene=re.compile(r"(?:promotional|branded|corporate|event|exhibition|convention|expo|trade.?show|retail|display).{0,30}(?:booth|stand|pavilion|stall|kiosk)|(?:booth|stand|pavilion).{0,28}(?:exhibition|branded|event|trade.?show|promotional)",re.I)
def score(row):
    title=str(row["name"] or "")
    description=str(row["description"] or "")
    caption=str(row["caption"] or "")
    if bad.search(title) or bad.search(description):return -10
    pts=0
    if explicit.search(title):pts+=9
    elif scene.search(title):pts+=5
    if explicit.search(description):pts+=5
    elif scene.search(description):pts+=3
    if explicit.search(caption):pts+=5
    elif scene.search(caption):pts+=3
    if row["category"]=="CAD_ARCHITECTURE":pts+=2
    if 6000<=int(row["face_count"] or 0)<=800000:pts+=1
    if int(row["material_count"] or 0)>=4:pts+=1
    return pts
data["quality_score"]=data.apply(score,axis=1)
good=data[(data.quality_score>=7)&(data.tar_order<=500)]
good=good.sort_values(["shard","tar_order","quality_score"],ascending=[True,True,False])
cols=["scene_id","name","caption","description","source_url","license_slug","author_username","category","face_count","material_count","file_name","shard","tar_order","quality_score"]
records=good[cols].fillna("").to_dict("records")
selection={"repo":DATASET,"known_uids_excluded":len(known),"all_rows":len(meta),"eligible":len(records),"candidates":records}
(out/"candidate_queue.json").write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding="utf8")
summary=good.groupby("shard").agg(count=("scene_id","count"),earliest=("tar_order","min"),best=("quality_score","max"))
summary=summary.sort_values(["count","earliest"],ascending=[False,True])
print("BULK_FILTER",len(data),"GOOD",len(good),"SHARD_COUNT",len(summary),flush=True)
for shard,row in summary.head(22).iterrows():
    examples=good[good.shard==shard].head(3)
    print("SHARD",shard,int(row["count"]),"EARLIEST",int(row["earliest"]),"EXAMPLES",examples.name.tolist(),flush=True)
