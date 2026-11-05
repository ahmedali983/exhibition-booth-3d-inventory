# ExpoVault × Sketchfab Backup

Integrated source repository: https://github.com/ahmedali983/sketchfab-backup
Original author: https://github.com/traines-source/sketchfab-backup
Git submodule: `integrations/sketchfab-backup` (MIT-licensed archiving code).

The GitHub fork contains **source code only**, not the external multi-terabyte model archive. Model ZIPs are externally hosted at https://mirror.traines.eu/sketchfab-backup/ . The mirror's author asks visitors not to bulk-download the whole mirror without coordination; request direct SMB/SSH permission for any large-scale transfer.

For a Sketchfab model UID `<uid>`, original public mirror resources, when present, follow:

- `https://mirror.traines.eu/sketchfab-backup/<first-two-chars>/<uid>.zip` (download archive; often `scene.gltf`, `scene.bin`, textures, `license.txt`, **not already a GLB**)
- `.../<uid>.source.zip` (author-uploaded native design source **when available**, not a guaranteed production file)
- `.../<uid>.thumb.jpeg` (preview)
- `.../<uid>.m.<slug>.json` (source model author, license, metadata).

All files remain subject to the original creator's individual license. Internal use alone does not authorize rehosting restricted assets. Keep attribution, source model links, rights and original hashes per model. Select complete professional exhibition booths only, exclude furniture, partial assets, repeated templates, and placeholders. Convert valid open glTF ZIPs to GLB for preview/download via a proper glTF converter while keeping the original assets. Do not invent native fabrication or engineering drawings; AI-derived preliminary fabrication ideas are separate.

As of November 5, 2026, independently verified on team Google Drive: 32 original-model ZIPs (18 original + 14 new), not 4,000:
https://drive.google.com/drive/folders/1pJNA1ZopzJ1ndTFmHlIvy_nMDQcOCMzL
https://drive.google.com/drive/folders/1voG47srN0fpkhiebxA6ua5tDR3HK6exP

After cloning ExpoVault:

```bash
git submodule update --init --recursive
```

This integration adds a Git reference only. It does **not** deploy a 3D collection, upload 55TB to Drive, or modify ExpoVault's customer-facing interface.
