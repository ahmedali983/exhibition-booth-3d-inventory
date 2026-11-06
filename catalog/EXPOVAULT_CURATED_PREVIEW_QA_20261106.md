# ExpoVault — honest curated preview QA, 2026-11-06

## Critical issue found
The earlier pilot showcased 369 source/archive IDs as though each had a meaningful booth preview. Several lacked actual preview images (green placeholders), several saved original files were modular components rather than fully designed booths. A source UID is **not** proof that a model is a complete, high-quality exhibition booth or that native CAD is production-certified.

## Implemented remediation
- Source-of-truth shortlist: `catalog/studio_quality_shortlist.json`.
- **Five** visual-preselected 3D designer booth models with working thumbnail images: MetaFactory, Croquet, OMIgroup, GM Hospitals and Stand Print Project.
- **One** WikiHouseNL WikiStand2014 built reference, with an actual GLB plus source SKP, DXF cut-file sets and PDFs. This is not an engineering certification.
- Five other designer booth candidates with black or unreliable thumbnail images removed from the main showcase.
- The remaining 369 IDs live in the collapsed **unreviewed archive**, which includes display components, modular shells, source files and other QA-stage models. They are **not** advertised as 369 production-ready booths.
- Official Sketchfab iframe viewer on original models, original-creator links, direct Sketchfab open fallback visible on every booth card and inside the modal.
- Composer's original source import (GLB or ZIP with a GLB), parts browser, brand recolouring and GLB export remain accessible and separate from view-only Sketchfab models.
- The public original GitHub Pages site at `https://ahmedali983.github.io/exhibition-booth-3d-inventory/` is unchanged.

## Browser QA evidence (Playwright on authorized Windows VM)
- Separate Vercel pilot homepage and Composer HTTP 200.
- Source shortlist manifest loads; **6 curated cards visible** (five designer booth thumbnails plus WikiStand).
- **6/6 selected previews** returned images with nonzero natural width. Scanned screenshots showed no green empty placeholder for selected cards.
- Unreviewed archive starts collapsed.
- Homepage mobile width 390px: no horizontal page overflow.
- Composer Three.js canvas loads, native GLB model can be selected and colour controls are present; previous end-to-end tests also verified colour pixel changes, GLB export integrity, and reimported model/item materials.
- All latest pilot scripts return JS rather than an SSO login HTML page.
- **Limitation:** Headless Chromium rendered Sketchfab model geometry in an iframe but also displayed `Something went wrong with the 3D viewer` after initialization. Therefore **in-site third-party Sketchfab 3D stability is not fully certified**. Direct `Open on Sketchfab` links were added as first-class fallback. This may be headless browser/WebGL-specific but was not ruled out.
- **Do not present as Sketchfab feature parity, full production-ready booth library or completion of the 1,000-real-booth goal.**

## Working user-facing pilot
https://expovault-internal-pilot.vercel.app/

Designer model original rights and branding/artwork use remain subject to per-author source terms. This pilot uses officially supported embedded viewing, **not** a viewer ripper or bypass of non-downloadable content.

Next acceptance gate: a genuinely independent interactive 3D viewer for the five shortlisted booth originals using authorized GLB source packages and permission to host; verify actual orbit/material controls and drawings, then add only additional proven full booth models.
