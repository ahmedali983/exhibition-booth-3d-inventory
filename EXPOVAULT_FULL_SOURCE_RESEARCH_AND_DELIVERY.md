# ExpoVault v0.4 — Source Acquisition + 3D Booth Composer Report
Date: 2026-11-04

## Executive outcome
ExpoVault now has a real 3D booth composer at https://ahmedali983.github.io/exhibition-booth-3d-inventory/composer.html.

It uses locally hosted GLB booth structures from 4,200 original procedural variations and 559 original CC0 GLB items. It allows a user to pick a booth, place and move items, change material colours, apply a brand name or image, then export one merged GLB or a concept ZIP with DXF and editable project JSON. This workflow never needs a Sketchfab login or a call to Sketchfab.

**Quality limitation:** The 4,200 stands are geometric parameter variations, not 4,200 independent professional architect-designed booths. The 559 Items are objects, display parts and props, not 559 complete production-approved stands. The 1,009 Sketchfab originals previously indexed are still metadata and approved embeds — their original meshes are NOT copied into ExpoVault.

## Complete acquisition options

| Route | Can we store original editable 3D locally? | Works without users signing in? | Requirements |
|---|---|---|---|
| Original booth designs built in Blender, SketchUp or our procedural tools | Yes | Yes | Own the full geometry and texture assets |
| CC0 model libraries such as 3DAssets and Poly Haven | Yes | Yes | Check CC0 status on each asset and ingest direct authorized files |
| Exact Sketchfab artist models supplied directly by their creators | Yes, with express rehosting rights | Yes after ingest | Signed authorization covering file storage, redistribution/download, modifications, and team use |
| Sketchfab integration/business agreement | May be possible, subject to agreement | Sketchfab invites inquiries about no-user-auth integrations | Obtain explicit API approval, comply with licences for every model |
| Standard Sketchfab Download API | glTF / GLB / USDZ of downloadable models only | Normally no | OAuth Sketchfab login; cannot infer standalone redistribution permission from download flag |
| Public GitHub 3D repositories | Sometimes | Yes | Verify licensing of art, not just software |
| Supplier/manufacturer CAD assets | Sometimes | Supplier-dependent | Manufacturing/supplier licence and CAD or dealer agreement |
| Paid modelling marketplaces / SketchUp Warehouse | Usually limited to use in a combined work | Provider-dependent | Check whether direct redistribution of standalone mesh is actually permitted |
| Reverse-engineering a view-only 3D embed | Not an appropriate source pipeline | Not supported | Does not give rehosting rights and violates source-platform restrictions; not implemented |

The user's noncommercial or internal-team intent does not automatically grant rights to store, extract or redistribute third-party 3D geometry. The exact Sketchfab models can be brought into ExpoVault when their owners or platform explicitly allow acquisition and direct file hosting.

## Useful source checks — verified 2026-11-04

1. Sketchfab Download API: https://sketchfab.com/developers/download-api — normal downloads require authentication; the platform provides an explicit contact route for integrations without end-user sign-in.
2. Sketchfab Download API integration guidelines: https://sketchfab.com/developers/download-api/guidelines — credit author/source and propagate licence. No blanket permission for rehosting third-party stand-alone files.
3. Sketchfab Terms of Use: https://sketchfab.com/terms — restrictions on scraping/aggregation/extraction, copies, reverse engineering and removal of viewer attribution.
4. Sketchfab downloaded formats: https://sketchfab.com/developers/download-api/downloading-models — temporary authorised glTF ZIP and USDZ links; FBX, MAX, SKP and OBJ originals not supplied by API.
5. 3DAssets.dev: https://3dassets.dev/docs and https://3dassets.dev/docs/api — CC0 public API and GLB files with self-contained geometry and materials. Already used for 559 hosted objects in ExpoVault.
6. Poly Haven: https://polyhaven.com/license — CC0 photogrammetry models, textures and HDRIs; rehosting assets permitted. API has separate terms, see https://github.com/Poly-Haven/Public-API/blob/master/ToS.md.
7. ambientCG: https://docs.ambientcg.com/license/ — CC0 PBR materials and some models, useful for realistic exhibit surfaces.
8. Kenney: https://kenney.nl/support — CC0 models, mainly stylised rather than realistic fabrication-grade stands.
9. Smithsonian Open Access: https://www.si.edu/openaccess — CC0-designated cultural 3D exhibits (not a major source of trade fair booths).
10. Blendkit: https://www.blendkit.com/docs/licenses/ — CC0 items can be reused but royalty-free licence is not a blanket mirror authorization.
11. Blender BlendSwap: https://blendswap.com/about — mixed Creative Commons licence per asset and account requirements.
12. SketchUp 3D Warehouse: https://help.sketchup.com/en/3d-warehouse/3d-warehouse-terms-use-faq — combined-work use may be permitted, but raw downloadable file republishing needs separate analysis/authorization.
13. Public GitHub design model repositories: may provide legitimate source files, but verify licence on model files, including texture sources, independently of repository-code licence.

## Implemented product details

### Booth Composer
Pages: composer.html, ui/composer.mjs, ui/composer.css.

- Select base footprint, exposure, structure style and interior setup; load real local GLB from the generated gallery.
- Search and insert any of the locally hosted CC0 Items; edit position X/Z, rotation and uniform scale; Shift-drag to move in the 3D canvas.
- Apply brand primary, trim/accent and wall/panel colours; add brand name or image; recolour individual material slots on placed Items.
- Download one assembled GLB including booth, objects and brand.
- Download a concept ZIP containing assembled GLB, original base DXF, full Item schedule/provenance, editable project JSON and warnings.
- Save and import project JSON for repeat editing.
- No Sketchfab session or Sketchfab viewer/network connection. The Three.js and JSZip frontend libraries are vendored with licence notices for reliable direct serving.

### Creator-authorised GLB ingestion
Script: scripts/ingest_authorized_booths.py.
Manifest example: catalog/authorized_import_example.json.
Catalog: catalog/authorized_booths.json.

Creators may supply a licensed GLB plus provenance, rights evidence and optional thumbnails. The script validates rights metadata and GLB 2.0 binary integrity, then stores assets under assets/authorized-booths for download from ExpoVault. The imported catalogue can be displayed in the no-login library. Initial count of approved original Sketchfab booth model files: **zero**. Do not represent the existing 1,009 reference thumbnails as local downloadable meshes.

### Creator outreach shortlisting
Script: scripts/build_creator_booth_shortlist.py.
Output: catalog/creator_booth_permission_shortlist.csv.
Ranks public Sketchfab model metadata for complete exhibition stands, records creator profile, original URL and existing licence flag, and marks every entry RIGHTS NOT VERIFIED. It is a lead list for permission requests, not a list of authorized local downloads.

## What actually makes a professional booth library

To reach the visual quality of high-end exhibition-showcase models, prioritize at least 50-100 **distinct** full-booth models at 3×3, 6×3, 6×6, 8×4 and 10×6 dimensions, with branded graphic panels, partition/wall architecture, furnishings, light fixtures and physically coherent scales. Prefer author-supplied native Blender/SKP/FBX plus a GLB conversion and explicit rights to store/redistribute their model files. Count substantive design differences, not simple colour and dimension variations.

You can also create professional original booths using a Blender geometry-node/parametric pipeline and curated CC0 realistic furniture and PBR surfaces; however, truly production-ready CAD requires independent supplier-compatible assemblies and engineering.

## Fabrication and rights caveats

- The assembled GLB is editable geometry for concept design, not certified manufacturing instructions.
- DXF in the ZIP is the **base booth** schematic only. Placed Items are documented in JSON but not incorporated into a verified 2D fabrication drawing.
- Actual cutting profiles, truss loads, fire safety, access, services/electrics and print bleeds must be approved separately.
- A paid or artist-downloaded model is not automatically distributable in standalone form.
- Per-creator attribution and licence must accompany CC BY and other attribution-bearing works when licensed for distribution.

## QA and delivery
Local Windows 11 VM Edge/Chromium tests: **15/15 passed** for the real 6×3 m booth, one inserted GLB item, transformation, brand colour, merged GLB download and integrity, project JSON save/reload, ZIP membership/CRC and mobile width.

Use the Live URL above for the functioning composer and the v0.4.0 GitHub Release for a fully packaged snapshot of the project and all hosted assets.
