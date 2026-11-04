# ExpoVault — Exhibition Booth 3D Inventory

An **open research catalogue** and **interactive 3D booth concept gallery**, built for exhibition / booth / trade-show research and quick brand-colour exploration.

**Launch gallery:** https://ahmedali983.github.io/exhibition-booth-3d-inventory/ (requires enabling GitHub Pages if not active).

## What is real, and what is not?

| Collection | What it contains | Count |
| --- | --- | --- |
| Procedural designs | Seven widths × six depths × four exposure types × five structure types × five fit-outs | **4,200 distinct parameter combinations** |
| Generated GLB + DXF | Actual geometry files and preliminary floor plans in \`assets/generated/\`; generated using \`scripts/generate_assets.py --all\` | **4,200 of each when the full generator is run** |
| External verified sources | Independently authored models, vendor CAD drawings, SketchUp Warehouse, paid markets and creator portfolios; original-page links and rights notes in \`catalog/sources.json\` | **25 manually curated source entries** |
| External searchable metadata | Model names, creator attribution, licence, original URLs and optional thumbnail via the official Sketchfab Data API, in \`catalog/sketchfab_index.json\` once harvested | **Count varies and is reported in that file** |

**IMPORTANT:** The 4,200 are **algorithmic variations of a small set of reusable booth systems**, not 4,200 original high-end architect designs. A record in the external index is not proof that the native CAD, CNC/print files, or even editable source \`.blend\` files exist. Never misrepresent a conceptual model as manufacturing-ready.

## Use the gallery

- Select width and depth in metres, booth exposure (inline/corner/peninsula/island), architectural style and internal fit-out.
- Pick a **white or black** base material and a **brand accent colour**.
- Enter a label for your brand; it appears on the live 3D mockup.
- Orbit / zoom / inspect the model, export **GLB** (true glTF 2.0 binary geometry), **OBJ**, **DXF preliminary plan**, or **JSON input spec**.
- Use **External 3D sources** to browse original, independently created model pages. Original files are not silently downloaded or mirrored.

## Build *actual* GLB + DXF files locally

Python 3.9+ with only the **standard library**:

\`\`\`bash
python scripts/generate_assets.py --limit 30
python scripts/generate_assets.py --all
\`\`\`

The second command creates **4,200 \`.glb\`** and **4,200 \`.dxf\`** files (sharded into width/depth folders), plus \`catalog/generated_manifest.json\`. These are original, programmatically generated concept geometries under CC0. They are low-poly; not a substitute for professionally designed and engineered booths. If the full generated directory is included in Git, it may make the repository larger and slower to clone.

## Grow the verified inventory from official sources

\`\`\`bash
python scripts/harvest_sketchfab.py --pages 4
\`\`\`

This script performs *public, documented Sketchfab Data API* metadata searches, checks \`isDownloadable\`, removes duplicate model UIDs, preserves author and license metadata, and writes \`catalog/sketchfab_index.json\`. It **does not download 3D models** or bypass authentication, paywalls or content rights. For Sketchfab original models, users must authenticate through Sketchfab and comply with per-model licences. No third-party model is distributed within this repository.

### Source provenance tiers

- **A — Hosted, generated**: Original procedurally generated GLB and DXF in this repo; editable mesh and preliminary plan. 
- **B — External free downloadable**: Creator download page is verified; the platform may require account login; licence and author travel with the model.
- **C — Vendor CAD**: Component details, not complete booth structural drawings; source licence may restrict redistribution.
- **D — Reference only**: Paid model, third-party source code without open licence, reference render, or listing with unclear availability; linked but not mirrored.

## Production safety

The geometry and DXF outputs are **concept drawings**. They are not certified or calibrated as shop drawings. Before making a physical stand, verify:
- exact site dimension / height limit and contractor exhibition rules
- panel system, dimensions, material thickness and joinery details
- structural loads, truss suspension and electrical safety
- fire regulations, accessibility and visitor routes
- actual CNC cutting sheets, print bleeds, artwork CMYK and DPI, assembly plans and bill of materials

## Run

Open \`index.html\` on GitHub Pages or host the root with \`python -m http.server 8000\`. The 3D editor loads Three.js 0.164.1 via jsDelivr import maps (internet required for first load).

## Licences

- Original generator script, site source and generated GLB/DXF concept assets: **CC0-1.0** (see \`LICENSE\`).
- Third-party linked assets: **remain owned and licensed by their creators**. Any CC BY asset needs author + source + licence attribution, including in downstream uses; paid or no-licence assets are not rehosted here.

## Next inventory targets

- Actual production-grade CAD (DWG/DXF) and parametric systems from manufacturers with explicit permission.
- Verified editable Blender / SketchUp / FreeCAD native project files.
- User-supplied or licensed print / cut / installation packs, tagged with dimensions and fabrication system.
