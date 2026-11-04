#!/usr/bin/env python3
"""ExpoVault: reproducible low-poly GLB + preliminary DXF booth concept generator.
Pure Python standard library. 4,200 distinct parameter combinations.
No third-party models, manufacturer's cut files, or certified drawings are included.
Usage: python scripts/generate_assets.py --all
       python scripts/generate_assets.py --limit 30
"""
import argparse
import itertools
import json
import math
import os
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parents[1]
WIDTHS = (3, 4, 5, 6, 8, 10, 12)
DEPTHS = (2, 3, 4, 5, 6, 8)
TYPES = ("Inline", "Corner", "Peninsula", "Island")
STYLES = ("Minimal", "Portal", "Truss", "Feature Wall", "Canopy")
FITS = ("Reception", "Meeting", "Retail", "Digital", "Storage")
PALETTE = (
    (0.92, 0.94, 0.96, 1.0),  # 0 main white
    (0.05, 0.72, 0.59, 1.0),  # 1 brand turquoise
    (0.67, 0.72, 0.77, 1.0),  # 2 floor
    (0.46, 0.55, 0.62, 1.0),  # 3 metal
    (0.08, 0.19, 0.27, 1.0),  # 4 dark screen
)

def cubes_for(v):
    w, d, typ, style, fit = v["width_m"], v["depth_m"], v["booth_type"], v["style"], v["fitout"]
    h = 3.2
    b = []
    def box(x, y, z, sx, sy, sz, mat=0):
        if min(sx, sy, sz) > 0:
            b.append((x, y, z, sx, sy, sz, mat))
    box(0, .06, 0, w, .12, d, 2)
    if typ != "Island":
        box(0, h / 2, -d / 2 + .07, w, h, .14)
    if typ == "Inline":
        box(-w / 2 + .07, h / 2, 0, .14, h, d)
        box(w / 2 - .07, h / 2, 0, .14, h, d)
    elif typ == "Corner":
        box(-w / 2 + .07, h / 2, 0, .14, h, d)
    if style in ("Portal", "Canopy"):
        box(-w / 2 + .14, h / 2, d / 2 - .16, .28, h, .3, 1)
        box(w / 2 - .14, h / 2, d / 2 - .16, .28, h, .3, 1)
        box(0, h - .17, d / 2 - .16, w, .35, .35, 1)
    if style == "Truss":
        for x in (-w / 2 + .18, w / 2 - .18):
            for z in (-d / 2 + .18, d / 2 - .18):
                box(x, (h + .25) / 2, z, .09, h + .25, .09, 3)
        for z in (-d / 2 + .18, d / 2 - .18):
            box(0, h + .25, z, w, .09, .09, 3)
        for x in (-w / 2 + .18, w / 2 - .18):
            box(x, h + .25, 0, .09, .09, d, 3)
    elif style == "Feature Wall":
        box(0, 1.75, -d / 2 + .3, min(w * .55, 4), 2.3, .22, 1)
        box(0, .5, -d / 2 + .48, min(w * .45, 3), .2, .45, 0)
    elif style == "Canopy":
        box(0, h + .06, 0, w * .9, .15, d * .65, 0)
    if typ == "Island":
        box(0, 1.1, 0, min(w * .42, 3), 2.2, .45, 1)
    if fit == "Reception":
        box(0, .53, d / 2 - .65, min(1.7, w * .5), 1.06, .66, 1)
        box(0, 1.07, d / 2 - .65, min(1.75, w * .5), .07, .72, 0)
    elif fit == "Meeting":
        box(0, .79, 0, min(1.65, w * .45), .08, .9)
        for x in (-.55, .55):
            for z in (-.35, .35):
                box(x, .38, z, .07, .75, .07, 3)
        for x in (-1.2, 1.2):
            box(x, .42, 0, .5, .8, .5, 1)
    elif fit == "Retail":
        for x in (-w * .23, 0, w * .23):
            box(x, .55, 0, .75, 1.05, .63)
            box(x, 1.1, 0, .8, .08, .68, 1)
    elif fit == "Digital":
        box(0, 1.85, -d / 2 + .28, min(w * .57, 3.4), 1.6, .1, 1)
        box(0, 1.85, -d / 2 + .21, min(w * .55, 3.28), 1.43, .07, 4)
        box(0, .52, d / 2 - .7, 1.5, 1, .7)
    elif fit == "Storage":
        box(w / 2 - .8, 1.2, -d / 2 + .82, 1.35, 2.4, .11, 1)
        box(w / 2 - 1.5, 1.2, -d / 2 + .17, .11, 2.4, 1.35)
        box(0, .54, d / 2 - .65, 1.2, 1.05, .6)
    return b

# Counter-clockwise triangles of a box in local coordinates, with outward normals.
FACES = (
    ((0, 0, 1), (4, 5, 6, 4, 6, 7)),
    ((0, 0, -1), (1, 0, 3, 1, 3, 2)),
    ((1, 0, 0), (5, 1, 2, 5, 2, 6)),
    ((-1, 0, 0), (0, 4, 7, 0, 7, 3)),
    ((0, 1, 0), (7, 6, 2, 7, 2, 3)),
    ((0, -1, 0), (0, 1, 5, 0, 5, 4)),
)
def make_glb(cubes):
    groups = [[] for _ in PALETTE]
    normals = [[] for _ in PALETTE]
    for x, y, z, sx, sy, sz, mat in cubes:
        corners = []
        for a, b, c in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):
            corners.append((x+a*sx/2,y+b*sy/2,z+c*sz/2))
        for normal, indices in FACES:
            for i in indices:
                groups[mat].extend(corners[i])
                normals[mat].extend(normal)
    payload = bytearray()
    views, accessors, primitives = [], [], []
    for mat, vertices in enumerate(groups):
        if not vertices:
            continue
        count = len(vertices) // 3
        offset = len(payload)
        payload += struct.pack("<" + "f" * len(vertices), *vertices)
        views.append({"buffer":0, "byteOffset":offset, "byteLength":len(vertices)*4, "target":34962})
        bounds = [vertices[i::3] for i in range(3)]
        posidx=len(accessors)
        accessors.append({"bufferView":len(views)-1,"componentType":5126,"count":count,"type":"VEC3",
                          "min":[min(v) for v in bounds],"max":[max(v) for v in bounds]})
        offset = len(payload)
        ns = normals[mat]
        payload += struct.pack("<" + "f" * len(ns), *ns)
        views.append({"buffer":0,"byteOffset":offset,"byteLength":len(ns)*4,"target":34962})
        normalidx = len(accessors)
        accessors.append({"bufferView":len(views)-1,"componentType":5126,"count":count,"type":"VEC3"})
        primitives.append({"attributes":{"POSITION":posidx,"NORMAL":normalidx},"material":mat,"mode":4})
    model={
        "asset":{"version":"2.0","generator":"ExpoVault stdlib geometry v1"},
        "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"name":"Exhibition Booth Concept","mesh":0}],
        "meshes":[{"primitives":primitives}],"materials":[{"name":"palette_"+str(i),
         "pbrMetallicRoughness":{"baseColorFactor":list(color),"metallicFactor":0.0,"roughnessFactor":0.76},
         "doubleSided":True} for i,color in enumerate(PALETTE)],
        "buffers":[{"byteLength":len(payload)}],"bufferViews":views,"accessors":accessors
    }
    json_chunk=json.dumps(model,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    json_chunk += b" " * ((-len(json_chunk)) % 4)
    payload += b"\x00" * ((-len(payload)) % 4)
    total=12+8+len(json_chunk)+8+len(payload)
    return struct.pack("<4sII",b"glTF",2,total)+struct.pack("<I4s",len(json_chunk),b"JSON")+json_chunk+struct.pack("<I4s",len(payload),b"BIN\x00")+payload

def make_dxf(v):
    w,d=v["width_m"]*1000,v["depth_m"]*1000
    lines=["0","SECTION","2","HEADER","9","$INSUNITS","70","4","0","ENDSEC","0","SECTION","2","ENTITIES"]
    def line(x1,y1,x2,y2,layer):
        lines.extend(["0","LINE","8",layer,"10",str(x1),"20",str(y1),"30","0","11",str(x2),"21",str(y2),"31","0"])
    def label(x,y,s):
        lines.extend(["0","TEXT","8","LABELS","10",str(x),"20",str(y),"30","0","40","160","1",s])
    line(0,0,w,0,"FOOTPRINT");line(w,0,w,d,"FOOTPRINT");line(w,d,0,d,"FOOTPRINT");line(0,d,0,0,"FOOTPRINT")
    if v["booth_type"]!="Island":line(0,0,w,0,"WALLS")
    if v["booth_type"] in ("Inline","Corner"):line(0,0,0,d,"WALLS")
    if v["booth_type"]=="Inline":line(w,0,w,d,"WALLS")
    line(0,-400,w,-400,"DIMENSIONS");line(-400,0,-400,d,"DIMENSIONS")
    label(w*.32,-850,"WIDTH "+str(w)+" MM");label(150,d+250,"DEPTH "+str(d)+" MM")
    label(150,d+520,v["id"]+" "+v["booth_type"]+" / "+v["style"]+" / "+v["fitout"])
    label(150,d+810,"CONCEPT ONLY - NOT A FABRICATION OR STRUCTURAL DRAWING")
    if v["fitout"] in ("Reception","Digital"):
        x=w/2
        for a,b,c,e in [(x-650,d-900,x+650,d-900),(x+650,d-900,x+650,d-300),(x+650,d-300,x-650,d-300),(x-650,d-300,x-650,d-900)]:
            line(a,b,c,e,"FURNITURE")
    lines.extend(["0","ENDSEC","0","EOF",""])
    return "\n".join(lines)

def specifications():
    number=0
    for w,d,typ,style,fit in itertools.product(WIDTHS,DEPTHS,TYPES,STYLES,FITS):
        number += 1
        ident = "EV-"+str(number).zfill(4)
        folder=f"assets/generated/{w}x{d}"
        yield {"id":ident,"width_m":w,"depth_m":d,"booth_type":typ,"style":style,
               "fitout":fit,"height_m":3.2,"area_m2":w*d,"glb":f"{folder}/{ident}.glb",
               "dxf":f"{folder}/{ident}.dxf","origin":"parametric-generated",
               "production_status":"PRELIMINARY_CONCEPT_NOT_MANUFACTURING_APPROVED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--all",action="store_true",help="Generate 4,200 full model + DXF pairs")
    p.add_argument("--limit",type=int,default=30,help="Generate first N models (default 30)")
    args=p.parse_args()
    limit=4200 if args.all else min(max(args.limit,1),4200)
    records=[]
    for n,v in enumerate(specifications(),1):
        if n>limit:break
        path=ROOT/v["glb"];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(make_glb(cubes_for(v)))
        (ROOT/v["dxf"]).write_text(make_dxf(v),encoding="ascii")
        records.append(v)
        if n%500==0:print(f"generated {n:,}/{limit:,}",flush=True)
    out=ROOT/"catalog"/"generated_manifest.json";out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"total":len(records),"license":"CC0 for generated files","note":"Procedural concepts; fabrication engineering not verified","items":records},indent=2)+"\n",encoding="utf-8")
    print(f"DONE: {len(records)} real GLB 2.0 files, {len(records)} DXF concept plans at {ROOT/'assets'/'generated'}")
if __name__=="__main__":main()
