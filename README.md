# ExpoVault — Self-Hosted Exhibition 3D Library

[**Open the live 3D gallery**](https://ahmedali983.github.io/exhibition-booth-3d-inventory/) · [**Edit a booth**](https://ahmedali983.github.io/exhibition-booth-3d-inventory/composer.html) · [**Browse locally hosted Items**](https://ahmedali983.github.io/exhibition-booth-3d-inventory/open-3d.html) · [**Open the team's Google Drive archive**](https://drive.google.com/drive/folders/1CSwu83cRerX6E1-kahJBUiu9XJqfuSZk)

**Verified November 5, 2026.** Only locally hosted original designer models appear as cards in the main gallery. There are no Sketchfab-viewer embeds in the current customer-facing gallery or Brand Studio. Every gallery model can be downloaded without a Sketchfab login. The separate original designer and generated concept collections are clearly distinguished.

## Verified inventory

| Collection | Number | Local GLB | 2D files | Important distinction |
|---|---:|---|---|---|
| Real exhibition stands authored by original designers, sourced from Objaverse's public Sketchfab-origin archive with live CC BY licence checks | **18** | **Yes**, editable GLB | **No authentic native DXF or DWG provided** | Each archive retains creator name, model URL and CC BY 4.0 attribution |
| CC0 Items, furniture and merchandising parts | **579** | **Yes** | No certified production drawings | 20 are not tagged AI-generated; 559 are tagged AI-generated in source metadata. Components, not 579 full booths |
| Procedural booth layout combinations | **4,200** | **Yes** | **4,200 conceptual DXF** | Variations of design rules, not 4,200 independently authored professional booths |
| External metadata-only references | ~1,009, retained for research | **No** except the 14 separately verified and hosted models | No | **Excluded** from the customer-facing gallery |
| Requested 6,000–8,000 independent professional booth designs | **Not currently available** | No | No | Not achieved. Never treat unrelated 3D objects as booth designs |

## How to use it

1. Visit [the original 3D gallery](https://ahmedali983.github.io/exhibition-booth-3d-inventory/). All 18 cards refer to locally hosted source-authored GLB geometry; click **Download** to receive a ZIP containing the GLB and creator credits. Click the card to inspect the model in our viewer.
2. Visit [Booth Composer](https://ahmedali983.github.io/exhibition-booth-3d-inventory/composer.html). Start with a generated booth **or choose from the 18 real designer booths**, apply your colours or logo, place [579 CC0 Items](https://ahmedali983.github.io/exhibition-booth-3d-inventory/open-3d.html), then export the assembled 3D GLB and editable JSON.
3. For a generated concept, also export a preliminary DXF floor plan. Original designer GLBs **do not contain original fabrication DXF or native SketchUp files** and we do not fabricate them.
4. To back up the real 3D files, use [Google Drive — original designer GLBs](https://drive.google.com/drive/folders/1pJNA1ZopzJ1ndTFmHlIvy_nMDQcOCMzL) (14 existing Drive ZIPs, with four new originals added to the live website pending the next Drive backup), or [Google Drive — CC0 Items](https://drive.google.com/drive/folders/1ba5s4BXjbltQT0fkmrOvpAu5QlFgsPcy) (nine category ZIPs and manifests). Team members need Drive permission; the website itself serves the verified models from GitHub Pages, not through Drive authentication.
5. Read the [Objaverse / ProSceneverse full corpus audit](https://drive.google.com/drive/folders/1stirgQhNquApqh4J-vprxT_A2cE3KshM).

## Reality check on the 8,000-booth target

We systematically scanned **798,759** Sketchfab-origin Objaverse models across 160 metadata shards. **708,311** were historically flagged downloadable with CC BY or CC0. Only **42** were strongly matched by explicit full-booth-related titles/descriptions; another **426** were loosely related to exhibition or retail scenes and **174** were candidate modular display items. These are *metadata results*, not acquired GLBs. Current rights and physical geometry must be checked individually.

In ProSceneverse, **74,624** scene descriptions include **52** explicit exhibition stand/booth matches among the **68,304** CC BY/CC0 scenes; broader terms match **2,517** mixed scenes, including stores, museums, galleries and games. Broad Objaverse and ProSceneverse candidates together have **3,593 unique model IDs**, not 3,593 complete professionally designed stands. The evidence does not justify a claim of 6,000–8,000 real complete booths.

Reproduce the research with `scripts/research_objaverse_all_shards.py` and `scripts/research_prosceneverse_census.py`, inspect `catalog/objaverse_all_800k_census.json` and `catalog/prosceneverse_booth_census_20261105.json`.

## Hosting, rights, and expansion

- **One-click local downloads:** The shipped original designer GLBs are source-authored model files retrieved from the public Objaverse archive. They are stored as site assets; the original designer and source licence follow each ZIP and derivative.
- **No login dependencies for team downloads:** No Sketchfab account, embeds or player extraction are used in the main gallery or Composer.
- **Sketchfab one-click Download API without end-user OAuth:** Requires a separate business/integrator arrangement. See [official guidance](https://sketchfab.com/developers/download-api/guidelines).
- **Noncommercial/internal use does not grant rights to rehost view-only models.** The application therefore does not copy models that prohibit downloads merely by extracting fragments from a public 3D player.
- **At scale, use an authenticated object-storage/CDN backend.** Private Google Drive is useful for backups, but not a direct anonymous file CDN. GitHub Pages has a published-site limit of 1 GB and a soft 100 GB/month traffic limit ([official docs](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)). Multiple thousands of high-fidelity original GLBs cannot sensibly stay in a single Pages deployment.
- To expand the collection, add a new author-supplied or openly licensed GLB plus creator metadata and licence evidence via `scripts/ingest_authorized_booths.py`, then update `catalog/authorized_booths.json`.

## Technical files

- Main gallery: `index.html`, `ui/v3.mjs`, `ui/v3.css`.
- Original GLBs: `assets/authorized-booths/SKFB-<uid>.glb`, metadata: `catalog/authorized_booths.json`.
- Composer: `composer.html`, `ui/composer.mjs`, `ui/composer.css`.
- CC0 Items: `assets/open-3d/*.glb`, metadata: `catalog/open_3d_cc0.json`.
- Parametric bases: `assets/generated/<size>/EV-xxxx.glb`, `*.dxf`.
- Source research audit and reproducibility: `catalog/objaverse_all_800k_census.json` and `scripts/research_objaverse_all_shards.py`.
- Historical third-party reference metadata remains under `catalog/sketchfab_index.json` and `catalog/creator_discovery.json` for rights research **only**, not as downloads.

**All exports are design concepts, not engineer-approved construction documents.**

## 2026-11-05: Strict real-booth acquisition gate

The target is **4,000 genuinely different professional complete exhibition booth designs**, not 4,000 pieces of furniture or 4,200 layout parameter combinations. This target is **not achieved**. There are currently **18 separately authored, source-licensed original exhibition booth GLBs** hosted and available for direct download, and the remainder of the 4,200 locally hosted generated designs must be counted separately.

The targeted public Sketchfab catalogue investigation found 311 candidate booth-related records from 19 queries, of which 89 had high-confidence complete-booth titles and 61 had matching GLB locations in the Objaverse historical public archive. Only four additional designs passed individual source, licence, GLB integrity, image and manual visual inspection and were incorporated in the library. Several other archived search results were variations of one near-identical stall design and should not be counted as diverse professional booths.

The real-booth pipeline is documented in `scripts/discover_real_exhibition_booths.py`, `scripts/ingest_curated_booth_batch.py`, and their matching record files in `catalog/`. Quality gate: complete booth visible in 3D; source-authored (not generated by the ExpoVault parametric system); meaningful stylistic uniqueness; current redistribution rights; self-contained valid GLB with texture/geometry; direct editable output and creator attribution.

The 5,000 mixed Objaverse search candidates discovered previously contain mostly fixture/retail object files and must not be advertised as professional full booths. For 4,000 diverse booths, the missing constraint is **asset supply and permission to store the native models**, not gallery pagination or a downloader button. Bulk supplier contracts or commissioned model packages are the realistic expansion path.
