#!/usr/bin/env python3
"""ExpoVault: import explicitly licensed creator GLB files into an offline-first vault.

This tool never calls Sketchfab's viewer, capture hooks, or protected endpoints.
Supply a locally acquired GLB or a permitted *direct* HTTPS file URL. A human must
verify the creator's redistribution grant before listing an asset in the manifest.

Examples:
    python scripts/ingest_authorized_booths.py --manifest catalog/authorized_import_example.json --dry-run
    python scripts/ingest_authorized_booths.py --manifest catalog/my_approved_models.json

Each imported model is then served from assets/authorized-booths/*.glb on your own
static site; visitors do not have to sign in to any source platform.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import pathlib
import re
import shutil
import socket
import sys
import tempfile
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "authorized-booths"
CATALOG = ROOT / "catalog" / "authorized_booths.json"
MAX_FILE = 90_000_000
ALLOWED_LICENSES = {
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "RIGHTS-HOLDER-PERMISSION": None,
}
BLOCKED_HOSTS = ("sketchfab.com", "sketchfab-prod-media.s3.amazonaws.com")

def safe_id(value: str) -> str:
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{2,64}",value):
        raise ValueError("Asset id must contain 3-65 safe characters (A-Z, 0-9, _ or -)")
    return value

def public_https(url: str) -> str:
    value = urllib.parse.urlsplit(str(url))
    host = (value.hostname or "").lower().rstrip(".")
    if value.scheme != "https" or not host or value.username or value.password:
        raise ValueError("Only unauthenticated public HTTPS file URLs are accepted")
    if any(host == blocked or host.endswith("." + blocked) for blocked in BLOCKED_HOSTS):
        raise ValueError("Use a creator-provided original download, not a protected Sketchfab URL")
    try:
        addresses = socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f"Unable to resolve host: {host}") from exc
    for entry in addresses:
        ip = ipaddress.ip_address(entry[4][0])
        if not ip.is_global:
            raise ValueError("Private, loopback or otherwise reserved IPs cannot be used")
    return str(url)

def read_file(record: dict, max_file: int) -> bytes:
    if "local_file" in record:
        source = (ROOT / record["local_file"]).resolve()
        if not source.is_relative_to(ROOT):
            raise ValueError("local_file must be inside the repository")
        if source.suffix.lower() != ".glb":
            raise ValueError("Only .glb input files are currently supported")
        if source.stat().st_size > max_file:
            raise ValueError("Asset exceeds maximum file size")
        return source.read_bytes()
    url = public_https(record["download_url"])
    req = urllib.request.Request(url,headers={"User-Agent":"ExpoVault-Licensed-Import/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:
        public_https(response.url)
        if response.status != 200:
            raise ValueError(f"Download HTTP {response.status}")
        data = response.read(max_file + 1)
    if len(data) > max_file:
        raise ValueError("File exceeds maximum file size")
    return data

def validate_glb(data:bytes) -> None:
    if len(data)<20 or data[0:4] != b"glTF":
        raise ValueError("Input is not a binary GLB file")
    if int.from_bytes(data[4:8],"little") != 2:
        raise ValueError("Only glTF 2.0 is supported")
    if int.from_bytes(data[8:12],"little") != len(data):
        raise ValueError("Incorrect embedded GLB byte length")
    if data[16:20]!=b"JSON":
        raise ValueError("GLB is missing the JSON scene chunk")

def validated_metadata(item: dict) -> dict:
    if not isinstance(item,dict):
        raise ValueError("Asset entry is not an object")
    identity = safe_id(item["id"])
    title = item["title"]
    creator = item["creator"]
    if not isinstance(title,str) or not title.strip() or not isinstance(creator,str) or not creator.strip():
        raise ValueError("title and creator are required")
    licence = item["license"]
    if licence not in ALLOWED_LICENSES:
        raise ValueError(f"License {licence!r} does not establish unrestricted file redistribution")
    if item.get("redistribution_checked") is not True:
        raise ValueError("A reviewer must explicitly confirm redistribution permission")
    if not isinstance(item.get("reviewer"),str) or len(item["reviewer"].strip())<2:
        raise ValueError("Record a responsible reviewer")
    proof = item.get("license_evidence_url")
    if not isinstance(proof,str) or not proof.startswith("https://"):
        raise ValueError("Provide a public licence / written creator-permission evidence URL")
    source_url = item.get("source_page")
    if not isinstance(source_url,str) or not source_url.startswith("https://"):
        raise ValueError("Source model page URL is required for provenance")
    if not item.get("download_url") and not item.get("local_file"):
        raise ValueError("A direct permitted download_url or local_file is required")
    if item.get("download_url"): public_https(item["download_url"])
    category = item.get("kind","booth")
    if category not in ("booth","item","stand-system","event-scene"):
        raise ValueError("Unknown kind; use booth, item, stand-system, event-scene")
    return {
        "id":identity,"name":title.strip(),"creator":creator.strip(),
        "license":licence,"license_url":ALLOWED_LICENSES[licence],
        "license_evidence_url":proof,"reviewer":item["reviewer"].strip(),
        "source_url":source_url,"kind":category,
        "description":str(item.get("description",""))[:700],
        "is_full_booth":bool(item.get("is_full_booth",False)),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest",required=True,type=pathlib.Path)
    parser.add_argument("--dry-run",action="store_true")
    parser.add_argument("--max-mb",type=int,default=90)
    args=parser.parse_args()
    src = args.manifest.resolve()
    if not src.is_file():
        parser.error(f"Manifest does not exist: {src}")
    items = json.loads(src.read_text(encoding="utf-8"))
    if isinstance(items,dict): items=items.get("assets",[])
    if not isinstance(items,list): raise ValueError("Manifest must be an array of assets")
    checked=[];identities=set()
    for raw in items:
        info=validated_metadata(raw)
        if info["id"] in identities: raise ValueError("Duplicate asset id "+info["id"])
        identities.add(info["id"])
        checked.append((raw,info))
    print("Preflight validated",len(checked),"manifest entries",flush=True)
    if args.dry_run:
        print("DRY RUN: no files downloaded or written")
        return
    max_size=min(max(1,args.max_mb),90)*1_000_000
    OUTPUT.mkdir(parents=True,exist_ok=True)
    staged=[];failures=[]
    for raw,metadata in checked:
        try:
            payload=read_file(raw,max_size)
            validate_glb(payload)
            destination=OUTPUT/(metadata["id"]+".glb")
            with tempfile.NamedTemporaryFile(dir=OUTPUT,delete=False,suffix=".tmp") as tmp:
                tmp.write(payload);temporary=pathlib.Path(tmp.name)
            temporary.replace(destination)
            metadata.update({
                "glb":"assets/authorized-booths/"+metadata["id"]+".glb",
                "file_size":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),
            })
            if raw.get("thumbnail_file"):
                thumb=(ROOT/raw["thumbnail_file"]).resolve()
                if not thumb.is_relative_to(ROOT):
                    raise ValueError("thumbnail_file must stay inside the repository")
                if thumb.suffix.lower()!=".webp":
                    raise ValueError("thumbnail_file must be a WebP image")
                image=thumb.read_bytes()
                if len(image)>3_000_000 or image[:4]!=b"RIFF" or image[8:12]!=b"WEBP":
                    raise ValueError("Invalid WebP thumbnail, max 3 MB")
                target=OUTPUT/(metadata["id"]+".webp")
                target.write_bytes(image)
                metadata["thumbnail"]="assets/authorized-booths/"+metadata["id"]+".webp"
            else:
                metadata["thumbnail"]=None
            staged.append(metadata)
            print("IMPORTED",metadata["id"],len(payload),"bytes",flush=True)
        except Exception as exc:
            failures.append({"id":metadata["id"],"error":str(exc)})
            print("SKIPPED",metadata["id"],str(exc)[:180],flush=True)
    # Existing records stay discoverable on subsequent incremental imports.
    existing=[]
    if CATALOG.is_file():
        existing=json.loads(CATALOG.read_text(encoding="utf-8")).get("assets",[])
    merged={entry["id"]:entry for entry in existing}
    merged.update({entry["id"]:entry for entry in staged})
    # Preserve source/permission records with every file.
    result={"name":"Authorized Booth 3D Library","count":len(merged),
            "note":"These files were separately obtained under verified redistribution licences or permission; not copied from embedded or restricted models.",
            "assets":sorted(merged.values(),key=lambda x:x["id"]),
            "last_import":{"added":len(staged),"skipped":len(failures),"failures":failures}}
    CATALOG.parent.mkdir(parents=True,exist_ok=True)
    CATALOG.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("DONE","total",len(merged),"new",len(staged),"failed",len(failures))
    if failures: sys.exit(1)

if __name__=="__main__":
    main()
