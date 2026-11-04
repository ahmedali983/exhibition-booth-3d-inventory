# ExpoVault — Exhibition Design Archive

Explore independent 3D exhibition models **inside ExpoVault**, try temporary brand colours in the live viewer, and work with thousands of separately hosted editable booth concepts.

**[Open the live gallery](https://ahmedali983.github.io/exhibition-booth-3d-inventory/)** · [3D Brand Studio](https://ahmedali983.github.io/exhibition-booth-3d-inventory/studio.html) · [All generated GLB + DXF files](https://github.com/ahmedali983/exhibition-booth-3d-inventory/releases/tag/v0.1.0)

## What's actually in the library?

| Asset group | Count | Where the data lives |
|---|---:|---|
| Sketchfab original creator listings | **1,009** | Model names, source IDs, authors, licences and catalogue metadata stored in this GitHub repository; 3D scenes embedded live from Sketchfab |
| Public high-resolution model thumbnail URLs | **1,009** | Stored in catalogue JSON; original image bytes remain on the Sketchfab CDN |
| Sketchfab listings marked downloadable | **299** | Downloads require Sketchfab authentication and the creator's licence; these files are not redistributed here |
| Procedurally generated booth layout combinations | **4,200** | Locally hosted in this repository, with original thumbnail images |
| GLB and DXF concept files | **4,200 GLB + 4,200 DXF** | Fully hosted here and bundled into a GitHub release ZIP |
| Independent manufacturer/CAD/marketplace source references | **35** | Local reference index links to original suppliers |

The 4,200 layouts combine 7 widths, 6 depths, 4 booth exposure types, 5 structural styles and 5 interior fit-outs. They are not 4,200 independent professional architectural designs. The 1,009 external models also include related display systems, kiosks, halls, pavilion and event assets; use the category filters to narrow to booths.

## What's new in v3

- **In-site Sketchfab 3D inspection:** open a model card to orbit and inspect the real 3D scene inside a full-size viewer without navigating away from ExpoVault.
- **Live material lab:** optionally use the [official Sketchfab Viewer API](https://sketchfab.com/developers/viewer/functions) to select an exposed material, choose a colour and try it *only in that live preview*. Reset reloads the untouched original scene. Texture-based materials can react differently.
- **Professional gallery:** high-resolution creator imagery via [Sketchfab oEmbed](https://sketchfab.com/developers/oembed), relevant-first feed, filters, download-status badges, search, keyboard support, next/previous navigation, shareable model deep-links and local saved collections.
- **Editable Concepts:** browse 4,200 original procedural GLB/DXF designs. Open any design in the brand studio with a direct URL to change its colours/logo and download a concept production ZIP.
- **Production Library:** supplier and CAD documentation indexed alongside general 3D references. These are references, not a transfer of third-party file licences.

## Important repo paths

- index.html, ui/v3.mjs, ui/v3.css — current user interface
- ui/material-lab.mjs — opt-in Sketchfab 3D material editing, browser session only
- studio.html and ui/app.mjs — parametric brand/customization studio
- catalog/sketchfab_index.json — 203 original source records
- catalog/creator_discovery.json — 806 additional model records
- catalog/oembed_thumbnails.json — 1,009 high-resolution oEmbed thumbnail URLs
- catalog/generated_manifest.json — parameters and direct GLB/DXF links for 4,200 generated items
- catalog/sources.json — 35 CAD, producer, marketplace and other research references
- assets/generated/ — 8,400 original generated GLB and DXF files
- assets/thumbs/ — 4,200 originally generated WebP booth thumbnails
- scripts/generate_assets.py — reproducible 3D/DXF generation
- scripts/render_thumbnails.py — reproducible original thumbnail generator
- scripts/enrich_sketchfab_thumbnails.py — public oEmbed metadata enrichment (no model geometry copied)

## Run and extend

Serve the repository root over HTTP using Python: `python -m http.server 8000`, then open `http://localhost:8000/`. For the generated design library, run `python scripts/generate_assets.py --all` (pure Python) and `python scripts/render_thumbnails.py` (Pillow required). Browsing source-hosted Sketchfab models requires internet.

## Source rights and production status

Sketchfab's [official Download API](https://sketchfab.com/developers/download-api/downloading-models) requires authenticated requests and only allows permitted downloads. We never bypass that, scrape protected meshes, or remove original viewer credit. The source model stays with the original artist. This project indexes public metadata, URLs and permitted embeds; **it does not host the original third-party geometry**.

Original ExpoVault code and procedurally generated mesh and plan files are CC0-1.0 per [LICENSE](LICENSE). Third-party content keeps its original creator licence regardless of whether it is embedded or linked.

**Production caveat:** our GLB, DXF, SVG panel guides and BOM estimates are preliminary concepts. They are not certified cutting sheets, final CMYK artwork, engineering/rigging plans or guaranteed build-ready geometry. Validate panel/frame tolerances, joinery, electrical, fire safety, accessibility and manufacturer specifications with an exhibition contractor.

---

ExpoVault · Learn, explore, adapt.
