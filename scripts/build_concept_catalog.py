#!/usr/bin/env python3
"""Create an efficient UI-only index of 4,200 original procedural booth concepts."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "catalog" / "generated_manifest.json").read_text(encoding="utf-8"))
out = {
    "format": "expovault-concept-cards-v1",
    "fields": ["id", "width_m", "depth_m", "booth_type", "style", "fitout", "area_m2"],
    "items": [
        [v["id"], v["width_m"], v["depth_m"], v["booth_type"], v["style"], v["fitout"], v["area_m2"]]
        for v in source["items"]
    ],
}
path = ROOT / "catalog" / "concept_cards.json"
path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Built {len(out['items'])} concise catalogue entries ({path.stat().st_size:,} bytes)")
