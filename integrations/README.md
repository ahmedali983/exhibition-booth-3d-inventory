# ExpoVault × Sketchfab Backup (source-code integration)

**Source repository in our GitHub account:** https://github.com/ahmedali983/sketchfab-backup  
**Linked in this repository as Git submodule:** `integrations/sketchfab-backup`  
**Original author:** https://github.com/traines-source/sketchfab-backup  
**Source code license:** MIT (see the submodule LICENSE).

## Important distinction

The GitHub fork contains the **Python archival code**, **not** the multi-terabyte 3D model archive.
The open Creative Commons / public-domain 3D assets remain hosted externally at:
https://mirror.traines.eu/sketchfab-backup/

GitHub does not hold all these models and the repo clone is small. Forking does not copy the external archive.

The mirror operator explicitly asks visitors **not to bulk-download the whole mirror**
without prior coordination. For larger collections ask the archive owner for bulk
SMB/SSH access. Only ingest models with a verified author license permitting reuse.
An internal-only use note is not a substitute for licensing.

## File naming convention on the public mirror

For source model ID `<uid>` (32-character hex), the mirror stores a folder based
on its first two characters:

`https://mirror.traines.eu/sketchfab-backup/<first-2-chars>/<uid>.zip`

This is typically the original Sketchfab-download ZIP: `scene.gltf`, `scene.bin`,
textures and `license.txt`, **not necessarily a ready-made GLB**.

The directory can also expose:

- `<uid>.source.zip` — **when available** the original creator-uploaded source,
  which may contain native files (formats vary); not a certified production plan
- `<uid>.thumb.jpeg` — original preview
- `<uid>.m.<slug>.json` — original Sketchfab model metadata including author,
  license, title and descriptions

The GitHub-forked Python script `integrations/sketchfab-backup/scrape.py` is the
upstream bulk-archive utility. It requires a valid Sketchfab token and should not
be treated as an anonymous download bypass.

## Current acquisition pipeline

1. Start with **booth IDs**, never blindly import millions of unfiltered models.
2. Verify metadata or original archive license; exclude non-downloadable, rights
   conflicts, and non-booths (props, furniture, stages, unfinished structures).
3. Prefer existing GLB from Objaverse; if the open backup only offers glTF ZIP,
   retain complete glTF/bin/textures and convert a separate GLB preview by a
   validated glTF tool. Preserve original source files unmodified.
4. If source ZIP is present, include it **separately and clearly labelled**, not
   as a fabricated production file. Only classify production-ready with actual
   fabricator-provided drawings and technical validation.
5. Deduplicate by model UID, file hashes and visual form.
6. Upload **only verified booth-specific model archives** to Google Drive,
   with title, creator, original URL and license in the manifest.
7. After reaching the requested 4,000 actual quality booth designs on Drive,
   separately build site integration. Do not inflate progress using generated
   variations or furniture components.

**Google Drive — originals (18 verified before new batches):**
https://drive.google.com/drive/folders/1pJNA1ZopzJ1ndTFmHlIvy_nMDQcOCMzL

**Google Drive — curated new model batches (14 verified):**
https://drive.google.com/drive/folders/1voG47srN0fpkhiebxA6ua5tDR3HK6exP

**Verification as of 2026-11-05:** 32 distinct source-authored model ZIPs on Drive,
not 4,000. The 55 TB external archive has not been copied to Google Drive or GitHub.

## Clone locally with the linked repo

```bash
git clone --recurse-submodules https://github.com/ahmedali983/exhibition-booth-3d-inventory.git
```

For an existing clone:

```bash
git submodule update --init --recursive
```
