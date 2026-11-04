#!/usr/bin/env python3
"""Refresh high-resolution public Sketchfab oEmbed thumbnail URL metadata.
Only publicly returned metadata is indexed. Source images and meshes remain on Sketchfab.

Usage:
    python scripts/enrich_sketchfab_thumbnails.py --workers 4 --limit 1009
    python scripts/enrich_sketchfab_thumbnails.py --workers 4 --resume

No OAuth tokens and no direct model archives are handled here.
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAT = ROOT / "catalog"
OUTPUT = CAT / "oembed_thumbnails.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def fetch_public_thumbnail(record):
    uid = record["id"][5:]
    page = "https://sketchfab.com/models/" + uid
    uri = "https://sketchfab.com/oembed?" + urllib.parse.urlencode({"url": page})
    try:
        req = urllib.request.Request(uri, headers={"User-Agent": "ExpoVault-Public-Metadata/3.0"})
        with urllib.request.urlopen(req, timeout=12) as reply:
            data = json.load(reply)
        img = data.get("thumbnail_url")
        if not isinstance(img, str) or not img.startswith("https://"):
            return None
        return record["id"], {
            "thumbnail": img,
            "width": data.get("thumbnail_width"),
            "height": data.get("thumbnail_height"),
        }
    except Exception as error:
        print("Unavailable:", record["id"], type(error).__name__, flush=True)
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=1009)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    source = load(CAT / "sketchfab_index.json")["items"] + load(CAT / "creator_discovery.json")["items"]
    known = {r["id"]: r for r in source}
    cache = {}
    if args.resume and OUTPUT.exists():
        cache = load(OUTPUT).get("thumbnails", {})
    remaining = [r for r in known.values() if r["id"] not in cache][:args.limit]
    print("Source models", len(known), "to query", len(remaining), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(1,args.workers),8)) as pool:
        for i, row in enumerate(pool.map(fetch_public_thumbnail,remaining), 1):
            if row:
                cache[row[0]] = row[1]
            if i % 80 == 0:
                print("Indexed", i, "of", len(remaining), "cached", len(cache), flush=True)
    output = {
        "source": "Official Sketchfab oEmbed metadata (no model files copied)",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "count": len(cache),
        "thumbnails": cache,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("Saved", len(cache), "thumbnail source URLs to", OUTPUT, flush=True)

if __name__ == "__main__":
    main()
