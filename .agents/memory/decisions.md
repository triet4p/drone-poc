# Decisions

## [2026-11-23] Pilot real Japanese rail point cloud from Commons + sparse COLMAP

**Decision:** Build the first real rail package from the Wikimedia Commons category
`Category:Yokokawa Station` using token-free Commons discovery and COLMAP sparse
reconstruction; use the identical pipeline on `Category:Nebukawa Station` as the reuse
test. Keep the existing Three.js picker and 7-float point layout; add observation-mode
packages (`points.bin` + `meta.json` + `observations.npz`) and return only recorded
`photo_id,u,v` observations on pick.

**Alternatives considered:** Mapillary/KartaView street-level discovery (token and/or
unverified Japan rail coverage; KartaView returned zero around Nebukawa/Tokyo); a real
FARO scan such as Alvord/ArchScanLib (not Japan rail; no photo poses; large downloads);
a cab-view video reconstruction (not arbitrary-location reusable); synthetic cloud plus
rendered views (violates the real-data requirement); Pi4 as the first reconstructor
(heavy CUDA install, NC weights, not needed to prove point-to-photo linkage).

**Reason:** Commons is the only token-free provider with verified named Japanese rail
categories (Yokokawa 53 files, Nebukawa 43). Sparse COLMAP directly yields the evidence
needed for click-to-photo: each 3D point carries the actual image keypoints that
triangulated it. This proves the reusable pipeline without depending on a paid scan,
Mapillary credentials, drone capture, or license decisions. The server has 54 GB free
and a 16 GB RTX 4060 Ti; sparse COLMAP can run CPU-first, with GPU optional.

**Consequences:** The pilot is limited to sites with enough overlapping Commons photos;
"any Japan rail location" means "traceable result or explicit coverage failure", not
guaranteed reconstruction. Scale defaults to `relative` because there is no GCP.
Mapillary/KartaView remain optional adapters. Pi4/dense MVS/drone are deferred. The
point/photo contract becomes multi-site and versioned; the synthetic B-14 package
remains as a labelled fallback, not the real-data demo.
