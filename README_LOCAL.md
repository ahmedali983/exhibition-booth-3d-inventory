# Run ExpoVault from your downloaded ZIP

This archive includes **4,200 locally hosted generated GLB meshes**, **4,200 preliminary DXF concept plans**, **4,200 original WEBP thumbnails**, an indexed catalogue of **1,009 Sketchfab creator-model metadata records**, high-resolution image URLs, and the website/editor source code.

## Run locally

1. Unzip the archive into a normal folder.
2. Windows: run `run_local.bat` (Python installed). macOS/Linux: run `sh run_local.sh`.
3. Open `http://127.0.0.1:8000/` in your web browser.

Opening `index.html` directly as `file://` is not supported because it fetches its local JSON indexes. A local HTTP server is needed. The website still requires internet for fonts, the Three.js JavaScript modules, and **all Sketchfab embedded models and creator-hosted images**.

## What's really local?

The 4,200 procedurally generated mesh/plan pairs, their thumbnail images, our scripts, and catalogue data are present in this ZIP. The 1,009 *external* Sketchfab models are **metadata and embed references only**, not copied third-party geometry. To import your own licensed model locally, open `/library.html` while the site is running and choose a GLB, OBJ, FBX or STL file. Saved imported assets live in the browser's IndexedDB, **not in the extracted ZIP folder**, and won't automatically sync to other computers.

## Limits

These generated DXF/SVG/BOM assets are concept handoffs rather than engineered fabrication plans. Third-party licences and permissions remain in force, even for educational use. Sketchfab's official viewer requires internet and does not grant source-download rights for view-only or paid models.
