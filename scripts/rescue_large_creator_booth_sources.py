from pathlib import Path
from io import BytesIO
import requests, re, json, zipfile, hashlib, subprocess, shutil, sys, html
from PIL import Image
UID=sys.argv[1]
assert re.fullmatch(r"[a-f0-9]{32}",UID)
base="https://mirror.traines.eu/sketchfab-backup/"+UID[:2]+"/"
out=Path("rescue-booth-"+UID);out.mkdir(exist_ok=True)
s=requests.Session();s.headers["User-Agent"]="ExpoVault-CC-Booth-Collection-Verified-Sources/1.0"
def fetch(url,limit):
 r=s.get(url,timeout=(15,95),stream=True);r.raise_for_status()
 sink=BytesIO()
 for data in r.iter_content(1024*1024):
  sink.write(data)
  if sink.tell()>limit:raise ValueError("File exceeds size limit")
 return sink.getvalue()
def inspect_zip(blob):
 z=zipfile.ZipFile(BytesIO(blob))
 if z.testzip():raise ValueError("Corrupted ZIP")
 if sum(x.file_size for x in z.infolist())>650000000:raise ValueError("Too many uncompressed bytes")
 for item in z.infolist():
  if item.filename.startswith("/") or ".." in Path(item.filename).parts:raise ValueError("Unsafe source archive entry")
 return z
html_dir=fetch(base,8000000).decode("utf8","replace")
links=re.findall(r'href="([^"]+)"',html_dir)
matches=[html.unescape(u) for u in links if re.fullmatch(UID+r'\.m\.[^"]+\.json',html.unescape(u))]
if len(matches)!=1:raise ValueError("Creator metadata absent or ambiguous: "+str(matches[:5]))
meta_url=base+matches[0]
raw_meta=fetch(meta_url,1000000);meta=json.loads(raw_meta)
lic=meta.get("license") or {}
label=str(lic.get("label") or "") if isinstance(lic,dict) else str(lic)
slug=str(lic.get("slug") or "") if isinstance(lic,dict) else ""
if re.search(r"no debe ser utilizado|without authorization|not for reuse|do not reupload|do not redistribute|do not use without permission",str(meta.get("description") or ""),re.I): raise ValueError("Explicit creator permission conflict")
if "noncommercial" in label.lower() or "no derivatives" in label.lower() or slug in ("by-nc","by-nd","by-nc-sa","by-nc-nd"):
 raise ValueError("License not suitable for redistribution or GLB conversion")
if slug=="cc0" or "public domain" in label.lower() or "cc0" in label.lower():
 lid="CC0-1.0";license_url="https://creativecommons.org/publicdomain/zero/1.0/"
elif slug=="by-sa" or "sharealike" in label.lower():
 lid="CC-BY-SA-4.0";license_url="https://creativecommons.org/licenses/by-sa/4.0/"
elif slug=="by" or label.strip().lower()=="cc attribution":
 lid="CC-BY-4.0";license_url="https://creativecommons.org/licenses/by/4.0/"
else:raise ValueError("Unknown license "+label+" "+slug)
user=meta.get("user") or {}
creator=str(user.get("username") or "") if isinstance(user,dict) else ""
if not creator:raise ValueError("Missing creator")
title=meta.get("name") or UID
original=fetch(base+UID+".zip",150000000)
source=fetch(base+UID+".source.zip",155000000)
preview=fetch(base+UID+".thumb.jpeg",3800000)
with Image.open(BytesIO(preview)) as im:im.verify()
gltf_archive=inspect_zip(original)
source_archive=inspect_zip(source)
scratch=out/"conversion";scratch.mkdir(exist_ok=True)
gltf_archive.extractall(scratch)
gltf_files=list(scratch.rglob("*.gltf"))
if len(gltf_files)!=1:raise ValueError("Missing glTF scene")
scene=json.loads(gltf_files[0].read_text(encoding="utf8"))
if not scene.get("meshes"):raise ValueError("No geometry")
glb=scratch/"model.glb"
proc=subprocess.run(["gltf-transform","copy",str(gltf_files[0]),str(glb)],capture_output=True,text=True,timeout=220)
if proc.returncode:raise RuntimeError("Conversion failed: "+proc.stderr[-180:])
glb_bytes=glb.read_bytes()
if glb_bytes[:4]!=b"glTF" or int.from_bytes(glb_bytes[4:8],"little")!=2 or int.from_bytes(glb_bytes[8:12],"little")!=len(glb_bytes):raise ValueError("Invalid GLB header")
n=int.from_bytes(glb_bytes[12:16],"little")
glb_data=json.loads(glb_bytes[20:20+n])
if not glb_data.get("meshes"):raise ValueError("GLB lost all geometry")
for chunk in list(glb_data.get("images") or [])+list(glb_data.get("buffers") or []):
 if chunk.get("uri") and not chunk["uri"].startswith("data:"):raise ValueError("External GLB dependencies")
uidname="SKFB-"+UID
source_names=[m.filename for m in source_archive.infolist() if not m.is_dir()]
manifest={"id":UID,"title":title,"creator":creator,"source_url":"https://sketchfab.com/models/"+UID,"license":lid,
"license_url":license_url,"archived_license":label,"metadata_source":meta_url,"model_source":base+UID+".zip",
"author_uploaded_source":base+UID+".source.zip","original_source_files":source_names[:120],
"native_source_status":"Author uploaded source. Production fabrication drawing is NOT verified.",
"original_mesh_count":len(glb_data["meshes"]),"glb_bytes":len(glb_bytes),"glb_sha256":hashlib.sha256(glb_bytes).hexdigest(),
"native_source_bytes":len(source),"native_source_sha256":hashlib.sha256(source).hexdigest(),
"preview_sha256":hashlib.sha256(preview).hexdigest()}
name=uidname+"-REAL-GLB-AND-CREATOR-SOURCE.zip"
package=out/name
with zipfile.ZipFile(package,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 z.writestr("ATTRIBUTION_AND_RIGHTS.txt",title+" by "+creator+"\n"+manifest["source_url"]+"\n"+lid+" "+license_url+"\nGLB converted from originally downloadable glTF with changes from original format. Source ZIP is NOT production-certified.\n")
 z.writestr("MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False))
 z.writestr("booth.glb",glb_bytes)
 z.writestr("original_creator_source.zip",source)
 z.writestr("preview.jpeg",preview)
with zipfile.ZipFile(package) as z:
 assert z.testzip() is None
 assert hashlib.sha256(z.read("booth.glb")).hexdigest()==manifest["glb_sha256"]
 if hashlib.sha256(z.read("original_creator_source.zip")).hexdigest()!=manifest["native_source_sha256"]:raise ValueError("Native source changed")
if package.stat().st_size>102000000:
 package.unlink()
 glb_archive=out/(uidname+"-GLB-ONLY.zip")
 with zipfile.ZipFile(glb_archive,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  z.writestr("MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False))
  z.writestr("booth.glb",glb_bytes)
  z.writestr("preview.jpeg",preview)
  z.writestr("ATTRIBUTION_AND_RIGHTS.txt",title+" by "+creator+"\\n"+manifest["source_url"]+"\\n"+lid+" "+license_url)
 source_archive_file=out/(uidname+"-CREATOR-SOURCE-ONLY.zip")
 with zipfile.ZipFile(source_archive_file,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  z.writestr("MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False))
  z.writestr("original_creator_source.zip",source)
  z.writestr("ATTRIBUTION_AND_RIGHTS.txt",title+" by "+creator+"\\n"+manifest["source_url"]+"\\n"+lid+" "+license_url)
 for f in [glb_archive,source_archive_file]:
  with zipfile.ZipFile(f) as z:assert z.testzip() is None
  if f.stat().st_size>97000000:raise ValueError("Individual source exceeds Drive cap")
 print("SPLIT_MODEL_ARCHIVES",UID,glb_archive.stat().st_size,source_archive_file.stat().st_size,flush=True)
else:
 print("PACKED_SINGLE_ARCHIVE",UID,package.stat().st_size,flush=True)
shutil.rmtree(scratch,ignore_errors=True)
print("COLLECTED",UID,title,creator,"PACKAGED_BYTES",(package.stat().st_size if package.exists() else "SPLIT"),"GLB",len(glb_bytes),"NATIVE",len(source),"ORIGINAL_COUNT",len(source_names),flush=True)
