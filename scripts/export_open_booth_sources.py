"""Archive ONLY two visually reviewed, CC Attribution designer booth models.
Uses openly mirrored licensed source archives; no UI rip, no protected download.
"""
import io,json,hashlib,zipfile,pathlib,subprocess,shutil,requests,sys
from PIL import Image
ROOT=pathlib.Path("expovault-drive-batch03");ROOT.mkdir(exist_ok=True)
BASE="https://mirror.traines.eu/sketchfab-backup/"
SEEDS=[
 ("401c0d92b8e1471cbc67c760d725dc1a","booth-design","Booth Design","Agung_Saragih"),
 ("50313afcb5154fb093c3df1ccb251aa5","booth-preliminary-design","Booth preliminary design","chrisfsd"),
]
SESSION=requests.Session();SESSION.headers["User-Agent"]="ExpoVault-CC-Original-Model-Source-Acquirer/1.0"
results=[];fails=[]
def safe_zip(b,maximum_unpacked=160_000_000):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  if z.testzip() is not None:raise ValueError("bad zip CRC")
  if sum(x.file_size for x in z.infolist())>maximum_unpacked:raise ValueError("zip extraction limit")
  for x in z.infolist():
   p=pathlib.PurePosixPath(x.filename)
   if p.is_absolute() or ".." in p.parts:raise ValueError("unsafe zip path")
 return True
def load(url,cap=70_000_000):
 with SESSION.get(url,timeout=(12,90),stream=True) as r:
  r.raise_for_status();buf=io.BytesIO()
  for chunk in r.iter_content(1024*1024):
   buf.write(chunk)
   if buf.tell()>cap:raise ValueError("max file limit exceeded")
  return buf.getvalue()
for uid,slug,title,artist in SEEDS:
 try:
  prefix=BASE+uid[:2]+"/"+uid
  meta_url=BASE+uid[:2]+"/"+uid+".m."+slug+".json"
  meta=SESSION.get(meta_url,timeout=20);meta.raise_for_status();j=meta.json()
  lic=j.get("license") or {}
  label=str(lic.get("label") or lic.get("slug") or "") if isinstance(lic,dict) else str(lic)
  creator=str((j.get("user") or {}).get("username") or "")
  if creator!=artist or ("attribution" not in label.lower() and label.lower()!="by") or "noncommercial" in label.lower():raise ValueError("CC BY source creator/license mismatch")
  raw=load(prefix+".zip",cap=45_000_000);safe_zip(raw)
  source=load(prefix+".source.zip",cap=35_000_000);safe_zip(source)
  preview=load(prefix+".thumb.jpeg",cap=3_000_000)
  image=Image.open(io.BytesIO(preview));image.verify()
  temp=ROOT/("tmp-"+uid);temp.mkdir()
  with zipfile.ZipFile(io.BytesIO(raw)) as z:z.extractall(temp)
  gltfs=list(temp.rglob("*.gltf"))
  if len(gltfs)!=1:raise ValueError("missing or ambiguous glTF")
  original=json.loads(gltfs[0].read_text(encoding="utf8"))
  if not original.get("meshes"):raise ValueError("missing mesh geometry")
  glb=ROOT/(uid+".glb")
  subprocess.run(["gltf-transform","copy",str(gltfs[0]),str(glb)],capture_output=True,text=True,timeout=80,check=True)
  b=glb.read_bytes()
  if b[:4]!=b"glTF" or int.from_bytes(b[4:8],"little")!=2 or int.from_bytes(b[8:12],"little")!=len(b):raise ValueError("bad converted GLB")
  jlen=int.from_bytes(b[12:16],"little");scene=json.loads(b[20:20+jlen])
  if not scene.get("meshes"):raise ValueError("converted GLB has no meshes")
  for entry in list(scene.get("images") or [])+list(scene.get("buffers") or []):
   if entry.get("uri") and not entry["uri"].startswith("data:"):raise ValueError("GLB has external resources")
  native_names=[]
  with zipfile.ZipFile(io.BytesIO(source)) as z:
   native_names=[x.filename for x in z.infolist() if not x.is_dir()][:100]
  manifest={"id":uid,"name":title,"creator":artist,"sketchfab":"https://sketchfab.com/models/"+uid,
      "license":"CC BY 4.0 (original archived metadata label: "+label+")","license_metadata":meta_url,
      "backup_url":prefix+".zip","source_zip_url":prefix+".source.zip",
      "glb_sha256":hashlib.sha256(b).hexdigest(),"glb_bytes":len(b),
      "gltf_zip_sha256":hashlib.sha256(raw).hexdigest(),
      "original_source_sha256":hashlib.sha256(source).hexdigest(),
      "native_source_members":native_names,"texture_count":len(scene.get("images") or []),
      "mesh_count":len(scene.get("meshes") or []),"production_status":"ORIGINAL_UPLOADED_SOURCE_ONLY_NOT_A_VERIFIED_FABRICATION_FILE",
      "review":"model geometry verified; visually reviewed on preview contact sheet; actual manufacturing suitability not assessed"}
  dest=ROOT/("SKFB-"+uid+"-ORIGINAL-CAD-AND-GLB.zip")
  with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
   z.writestr("LICENSE_AND_ATTRIBUTION.txt",title+"\nOriginal creator: "+artist+"\nOriginal source: "+manifest["sketchfab"]+"\nCreative Commons Attribution 4.0: https://creativecommons.org/licenses/by/4.0/\nOriginal native uploaded source is not verified build documentation.\n")
   z.writestr("MODEL_MANIFEST.json",json.dumps(manifest,ensure_ascii=False,indent=2))
   z.write(glb,arcname="model.glb")
   z.writestr("original_sketchfab_gltf_download.zip",raw)
   z.writestr("original_creator_source.zip",source)
   z.writestr("original_preview.jpeg",preview)
  with zipfile.ZipFile(dest) as z:
   assert z.testzip() is None
   assert hashlib.sha256(z.read("model.glb")).hexdigest()==manifest["glb_sha256"]
  results.append({**manifest,"archive_name":dest.name,"archive_bytes":dest.stat().st_size})
  print("READY",uid,title,"GLB",len(b),"NATIVE_SOURCE",len(source),"BUNDLE",dest.stat().st_size,flush=True)
  shutil.rmtree(temp,ignore_errors=True);glb.unlink(missing_ok=True)
 except Exception as ex:
  fails.append({"uid":uid,"reason":str(ex)[:220]})
  print("FAIL",uid,str(ex)[:220],flush=True)
(ROOT/"BATCH03_INDEX.json").write_text(json.dumps({"count":len(results),"success":results,"failures":fails},ensure_ascii=False,indent=2),encoding="utf8")
if not results:sys.exit("No source asset passed all checks")
