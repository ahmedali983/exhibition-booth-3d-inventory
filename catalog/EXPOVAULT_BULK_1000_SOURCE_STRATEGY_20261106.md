# ExpoVault — 1,000 genuine, professionally usable booth designs: evidence & bulk sourcing

Updated 2026-11-06. **Current 3D archival stage: 224 source-authored distinct model UIDs on private team Drive. This is NOT a 224 professional-complete-booth acceptance count.** Work remains on design uniqueness, full booth geometry, visual quality, rights, and actual fabrication readiness.

## Verified actual acquisitions
- Baseline 204 (through Wave11).
- Wave12 16 new independently integrity-validated packages on Drive: https://drive.google.com/drive/folders/1xB8WjXGLwKxtn8_0rmKL6eodI5r8fJF3
- Wave13 4 new integrity-validated model IDs, including one oversized 20x30 trade-show booth author source split into two byte-perfect chunks: https://drive.google.com/drive/folders/1YJi2JbZgwGLT3pqQhPESFKFftZjeaRKy
- UIDs and tally: catalog/expovault_known_uids_224_20261106.json
- GitHub runs: https://github.com/ahmedali983/exhibition-booth-3d-inventory/actions/runs/42166841736 and https://github.com/ahmedali983/exhibition-booth-3d-inventory/actions/runs/42168248417

## Existing openly-licensed research pipeline
- Official Sketchfab public API 10-market multilingual catalog scan, after exclusion of known 204 -> 523 new candidate records, only 30 highly relevant titles. None of those candidate records alone is a physical design. See catalog/worldwide_licensed_booth_candidates_20261106.json.
- Four GitHub cloud runner HEAD-check shards found 483 historical original glTF + creator source archive URLs (public, source-authorized at archival point). Source files/author thumbnails still require current author-rights checks, geometry QA, and manual visual classification.
- Source gathering uses direct archives for models with archived Creative Commons distributions, never extracting a Sketchfab viewer or a view-only asset. Creator description restriction wins over a prior CC label. Example: "Expo Stand Chidas" rejected with an explicit author restriction.
- Official Sketchfab Download API: requires authenticated end-user (OAuth) unless special integrator agreement. It can support legitimate links/download experience at scale but does not make locked models downloadable: https://sketchfab.com/developers/download-api/guidelines
- Technical cap: official API catalog search returns at most 24 results per page; pagination and 429 backoff are necessary. https://docs.sketchfab.com/data-api/v3/index.html

## Significant candidate commercial inventory: requires separate permission for native files

1. CGTrader exhibition-stand listings: https://www.cgtrader.com/3d-models/exhibition-stand (live listing indicates ~35,060; count includes irrelevant furniture, accessories and templates, and does not represent 35k professional booths).
2. moarrefiii creator pack: https://www.cgtrader.com/3d-model-packs/massive-exhibition-collection-vol-massive1 (listed 87 3D models for $250 full price, periodic discount, exact dedup/quality to verify).
3. FLcovers booth pack: https://www.cgtrader.com/3d-model-packs/booth-design-collection (listed 30 models for $138 full price).
4. vBoothify physical scaled .max show stand designs: https://vboothify.com/ (states free commercial design-project usage; ***not*** a proven license for redistributing the standalone source model files in a downloadable library).
5. Community CC0 3D asset registry: https://github.com/toxsam/open-source-3D-assets (991+ general props; not 991 complete professional booths; should be in Items collection, not Booth collection).

**Stop condition**: CGTrader standard Royalty Free model license does NOT permit independent re-distribution of raw model files, including creating a new download library. No automated bulk archiving without expanded written rights. Source: https://www.cgtrader.com/pages/terms-and-conditions

## High-throughput route with actual authenticity
- Negotiate a bulk **original model-file license** with multi-booth creators / exhibition design agencies, explicitly permitting team storage, repeat download by staff, modification, inclusion in an ExpoVault interface, and downstream client use as appropriate. Agree model count, distinct geometry, file native formats, textures, rights provenance, source-model releases, and pricing.
- Demand 100 models/sample first. Verify a sample of 20 files in Blender by three-angle orbit, visible roof/frame, visitor access, reception/branding, technical scale, file hashes, model format compatibility. Detect near-identical designs before the 1,000 target count.
- Obtain model ZIPs via owner-supplied cloud bucket, signed export, Git LFS or download links. Parallel-batch import with checkpoints, SHA256, safe ZIP extraction, GLB conversion, source archive preservation, explicit rights manifest, duplicate detection. Upload to Drive in groups with accurate staging and accepted counts.
- Keep separate counts: (a) candidate metadata, (b) downloaded original source 3D, (c) correct redistribution permission, (d) semantically unique full physical booth, (e) manufacturer/CAD verified. Never substitute one for another.
- Large files: split byte-for-byte into <=80MiB parts, preserve checksum + reassembly instructions; never discard original author source. Do not use a viewer ripper or non-downloadable content.
- 1,000 distinct, completed, genuine booth designs cannot be verified from current openly licensed evidence alone. An explicit supplier acquisition is the feasible bulk step.

## Site handling
Do not push bulk assets to the live Github Pages gallery or merge source branch before manual acceptance. Existing source model files stay on Google Drive QA staging, with a separate limited catalog for verified customer-facing assets.
