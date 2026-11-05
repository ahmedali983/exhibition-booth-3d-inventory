#!/usr/bin/env python3
"""Metadata-only aesthetic-filtered source discovery; never assumes permission to rehost.
TRELLIS lists aesthetic-scored source 3D assets but does not itself transfer ownership.
"""
import csv,os,re,json,requests,sys,time
from pathlib import Path
from urllib.parse import urlparse
URL="https://huggingface.co/datasets/JeffreyXiang/TRELLIS-500K/resolve/main/ObjaverseXL_github.csv"
OUT=Path("trellis-github-booth-scan")
OUT.mkdir(exist_ok=True)
strong=re.compile(r"\b(exhibition\s+(booth|stand|stall)|trade\s*(show|fair)\s+(booth|stand)|expo\s+(booth|stand|stall)|fair\s+(booth|stand)|convention\s+booth|custom\s+exhibition|brand\s+activation\s+booth|messestand|messebau|fuar\s+stand[ıi]?|выставочн.{0,18}стенд|stand\s+(de\s+)?feria|stand\s+d.exposition|estande\s+(de\s+)?feira|展位|展台)\b",re.I)
wide=re.compile(r"\b(booth|pavilion|kiosk|exhibition|expo|fuar|fair\s+stand|display\s+stand|trade\s+show|stall|shopfront|showroom)\b",re.I)
reject=re.compile(r"photo\s+booth|dj\s+booth|voting\s+booth|telephone\s+booth|toll\s+booth|phone\s+booth|bus\s+stand|food\s+stall|fruit\s+stand|medieval|minecraft|fortnite|roblox|game\s+asset|nightstand|beach\s+stand",re.I)
all_rows=0;hits=[];broad=[];examples=[]
print("DOWNLOAD_META",URL,flush=True)
res=requests.get(URL,stream=True,timeout=(30,160),headers={"User-Agent":"ExpoVault-Aesthetic-Open-3D-Metadata-Research/1.0"})
res.raise_for_status()
import tempfile
with tempfile.NamedTemporaryFile(mode="w+b",suffix=".csv") as file:
    total=0
    for c in res.iter_content(1024*1024):
        if not c:continue
        total+=len(c)
        if total>300_000_000:raise RuntimeError("unexpected dataset size")
        file.write(c)
    file.flush();file.seek(0)
    stream=(line.decode("utf-8-sig","replace") for line in file)
    reader=csv.DictReader(stream)
    fields=reader.fieldnames
    print("CSV_FIELDS",fields,"BYTES",total,flush=True)
    for row in reader:
        all_rows+=1
        if all_rows<=2:examples.append({k:str(v)[:250] for k,v in row.items()})
        values=" ".join(str(v or "") for v in row.values())
        if reject.search(values) and not strong.search(values):continue
        matched=strong.search(values)
        if matched or wide.search(values):
            record={"row":all_rows,**{k:str(v or "")[:2000] for k,v in row.items()}}
            if matched:record["match"]=matched.group(0);hits.append(record)
            else:broad.append(record)
        if all_rows%50000==0:print("SCANNED",all_rows,"STRONG",len(hits),"BROAD",len(broad),flush=True)
print("SCAN_DONE",all_rows,len(hits),len(broad),flush=True)
report={"source":URL,"source_kind":"metadata only, original 3D licensing still requires verification",
"total_aesthetic_filtered_records":all_rows,"strong_title_caption_matches":len(hits),
"broad_matches":len(broad),"fields":fields,"example_rows":examples,"strong":hits[:3000],"broad":broad[:1500]}
(OUT/"trellis_booth_matches.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
with (OUT/"trellis_booth_matches.csv").open("w",newline="",encoding="utf8") as f:
    writer=csv.writer(f);writer.writerow(["strength","row_number","source_fields"])
    for row in hits[:3000]:writer.writerow(["strong",row["row"],json.dumps(row,ensure_ascii=False)])
    for row in broad[:1500]:writer.writerow(["broad",row["row"],json.dumps(row,ensure_ascii=False)])
for row in hits[:32]:
    print("STRONG_HIT",json.dumps(row,ensure_ascii=False)[:950],flush=True)
