# Plan — real rail inspection demo

## Goal
Real photographs and a real point cloud at a real Japanese rail site, with layered
3D map/point-cloud/photo UI and a reusable acquisition → inference → reconstruction
pipeline. Drone is optional. License selection deferred.

## Milestones
1. Multi-source acquisition (Commons, video, Mapillary, uploads) — merge into one site.
2. Sparse evidence package (COLMAP track) — Koma River Bridge PASS.
3. Dense/visual point cloud — COLMAP CUDA build, fallback VGG-T³/Pi4.
4. Lateral-view site — Mapillary/Commons/OSM combination beyond cab-view.
5. Layered viewer — 3D map, dense cloud, sparse clickable points, photos, filters,
   default camera preset.
6. Inference integration — real images → existing Grounding DINO, tied to photo_id.

## Current state (2026-11-23)
- Koma COLMAP sparse package: 34 frames, 993 points, 4,460 observations, 0.716 px.
- Mapillary SfM cluster: 6,041 points / 26 photos / 17,920 projected observations,
  but sampled cluster is street-level, not rail — not promoted.
- VGG-T³: 31,442 points / 16 frames, cloud compact; fallback only.
- Multi-source merge CLI implemented; Koma video+Mapillary merge failed COLMAP.
- UI: point highlight, local coords, reset view, layer toggles (cloud/grid/photo).
- COLMAP CUDA build in progress (GCC 12 + CUDA 12.1).

## Detailed sprint
`docs/sprint-plans/sprint-26.md`
