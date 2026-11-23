# Sprint 26 — real rail data, dense and layered

Status: `[~]` in progress. Owner: Main. Workflow: lightweight, one integration owner.

## Acceptance
- [x] Multi-source manifest merge (Commons/video/Mapillary) with provenance.
- [x] Sparse COLMAP package for a real Japanese rail site (Koma).
- [ ] Dense point cloud or recognizable surface for the primary site.
- [ ] At least one site with lateral viewpoints, not only cab-view.
- [ ] Layered viewer: 3D map + point cloud + photos, toggles/filter, default camera.
- [x] Pi4 and VGG-T³ fallbacks documented on Koma frames.
- [ ] Dense/multi-source click still opens the exact source photo and marker.

## Tasks
- [x] Multi-source `merge` CLI.
- [x] Mapillary `sfm_cluster` adapter and trial (cluster street-level; not promoted).
- [x] Mapillary SfM cluster adapter (`sfm_cluster` zlib → package).
- [x] VGG-T³ 16-frame fallback package.
- [x] UI selected-point highlight, local coords, reset, layer toggles.
- [x] Robust percentile camera framing; dense layer hooks.
- [x] COLMAP CUDA build → dense Koma MVS.
- [x] Dense PLY → `dense.bin` visual layer + sparse clickable overlay.
- [ ] Candidate lateral site (Tokyo/Odawara/other) with Mapillary + Commons.
- [ ] MapLibre base map layer in the same scene.
- [x] Pi4 install/run on 16 Koma frames (27,437 points, 89 s); not promoted.

## Gates
- Dense: visually recognizable track/bridge, source photo mapping preserved.
- Lateral site: at least 6 registered views, click evidence 20/20.
- UI: layer toggles do not hide the selected-point marker; reset returns to preset.
