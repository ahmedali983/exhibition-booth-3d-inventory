import requests, pathlib, json, io, hashlib, zipfile, subprocess, shutil, sys
from PIL import Image
OUT=pathlib.Path("archive-three-booths")
OUT.mkdir(exist_ok=True)
BASE="https://mirror.traines.eu/sketchfab-backup/"
SEEDS=[
 ("40359de9049b4a47afe5762da5546005","bobcat-trade-show-booth","Bobcat Trade Show Booth"),
 ("80e40d1e173d4e6ba84a984c3c2aa09d","adamvs-exhibition-booth","ADAMVS Exhibition Booth"),
 ("401c0d92b8e1471cbc67c760d725dc1a","booth-design","Booth Design"),
]
session=requests.Session()
session.headers["User-Agent"]="ExpoVault-CC-booth-archival-inventory/1.0"
def get(url,limit):
    res=session.get(url,timeout=(15,90),stream=True)
    res.raise_for_status()
    b=io.BytesIO()
    for c in res.iter_content(1024*1024):
        b.write(c)
        if b.tell()>limit:raise ValueError("Too large")
    return b.getvalue()
def safe_zip(blob):
    z=zipfile.ZipFile(io.BytesIO(blob))
    if z.testzip():raise ValueError("Corrupt ZIP")
    if sum(x.file_size for x in z.infolist())>220_000_000:raise ValueError("Exceeds extraction limit")
    for x in z.infolist():
        parts=pathlib.PurePosixPath(x.filename).parts
        if x.filename.startswith("/") or ".." in parts:raise ValueError("Unsafe name")
    return z
results=[]; errors=[]
for uid,slug,title in SEEDS:
    try:
        root=BASE+uid[:2]+"/"+uid
        metadata=get(root+".m."+slug+".json",2_000_000)
        j=json.loads(metadata)
        lic=j.get("license") or {}
        if isinstance(lic,dict):
            label=str(lic.get("label") or "")
            license_slug=str(lic.get("slug") or "")
        else:label=str(lic);license_slug=""
        user=j.get("user") or {}
        artist=user.get("username") if isinstance(user,dict) else None
        if not artist or ("attribution" not in label.lower() and license_slug!="by"):
            raise ValueError("Unable to confirm CC Attribution license and artist")
        if "noncommercial" in label.lower():raise ValueError("Noncommercial source excluded")
        gltf_download=get(root+".zip",85_000_000)
        native_download=get(root+".source.zip",85_000_000)
        preview=get(root+".thumb.jpeg",4_000_000)
        with Image.open(io.BytesIO(preview)) as im:im.verify()
        gltf_zip=safe_zip(gltf_download)
        source_zip=safe_zip(native_download)
        folder=OUT/uid;folder.mkdir(exist_ok=True)
        gltf_zip.extractall(folder)
        gltfs=list(folder.rglob("*.gltf"))
        if len(gltfs)!=1:raise ValueError("Unexpected glTF file count")
        raw=json.loads(gltfs[0].read_text(encoding="utf8"))
        if not raw.get("meshes"):raise ValueError("No meshes")
        glb=folder/"model.glb"
        run=subprocess.run(["gltf-transform","copy",str(gltfs[0]),str(glb)],capture_output=True,text=True,timeout=120)
        if run.returncode:raise RuntimeError("glTF conversion failed: "+run.stderr[-250:])
        data=glb.read_bytes()
        if data[:4]!=b"glTF" or int.from_bytes(data[4:8],"little")!=2 or int.from_bytes(data[8:12],"little")!=len(data):raise ValueError("Invalid GLB")
        chunk_size=int.from_bytes(data[12:16],"little")
        scene=json.loads(data[20:20+chunk_size])
        if not scene.get("meshes"):raise ValueError("GLB geometry missing")
        source_names=[x.filename for x in source_zip.infolist() if not x.is_dir()]
        source_link="https://sketchfab.com/models/"+uid
        sha=hashlib.sha256(data).hexdigest()
        info={"uid":uid,"title":title,"creator":artist,"source_url":source_link,"license":"CC BY 4.0",
              "archived_license":label,"attribution":"Creator "+artist+", source "+source_link,
              "GLB_sha256":sha,"GLB_bytes":len(data),"GLB_mesh_count":len(scene["meshes"]),
              "original_gltf_download_bytes":len(gltf_download),"original_creator_source_bytes":len(native_download),
              "original_source_filename_list":source_names[:100],"production_file_status":"Original author source present; engineering fabrication documents NOT certified",
              "license_metadata_url":root+".m."+slug+".json"}
        archive=OUT/("SKFB-"+uid+"-GLB-SOURCE.zip")
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
            z.writestr("ATTRIBUTION_AND_RIGHTS.txt",title+" by "+artist+"\n"+source_link+"\nCC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nNative source not certified for fabrication.\n")
            z.writestr("MANIFEST.json",json.dumps(info,indent=2,ensure_ascii=False))
            z.writestr("model.glb",data)
            z.writestr("original_gltf_with_textures.zip",gltf_download)
            z.writestr("original_creator_source.zip",native_download)
            z.writestr("preview.jpeg",preview)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            assert hashlib.sha256(z.read("model.glb")).hexdigest()==sha
        results.append({**info,"archive_name":archive.name,"archive_bytes":archive.stat().st_size})
        print("VERIFIED_ARCHIVED",uid,len(data),archive.stat().st_size,"source_files",len(source_names),flush=True)
        shutil.rmtree(folder,ignore_errors=True)
    except Exception as e:
        errors.append({"uid":uid,"error":str(e)[:350]})
        print("REJECT",uid,str(e)[:350],flush=True)
(OUT/"COLLECTION_INDEX.json").write_text(json.dumps({"count":len(results),"assets":results,"errors":errors},indent=2,ensure_ascii=False),encoding="utf8")
if not results:sys.exit("No authorized original bundle successfully processed")
