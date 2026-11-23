# Real rail pilot results (2026-11-23)

Status: **one real package passed geometry gates**; Mapillary adapter implemented and
under evaluation. All coordinates/claims below are from the actual runs, not projections.

## 1. Yokokawa Station (Commons stills) — failed, recorded

- Source: `Category:Yokokawa Station`, 44 usable files at 500 px from cached Commons
  thumbnails (higher-resolution downloads were rate-limited by Wikimedia).
- COLMAP: 44 images, 946 pairs, one 440-inlier pair; mapper found no non-degenerate
  initial pair. `two_view_geometries.config=6` (planar/panoramic) on the strongest pair.
- Same-era 1997 subset (8 files) behaved the same: no non-degenerate initial pair.
- Conclusion: `insufficient_overlap` for this Commons set. The images are mostly
  platform/interior/panorama views, not a translating walkaround. Do not merge eras or
  lower the click definition to force a result.
- Preserved work: `data/rail/yokokawa/`, `data/rail/yokokawa_1997/`; logs on the remote
  at the same paths.

## 2. Koma River Bridge, Hachiko Line, Saitama — passed

- Real site: 高麗川橋梁, 八高線, between 高麗川 and 毛呂, Saitama, Japan.
- Source: YouTube `Cu7dfjXOVQY` ("八高線 高麗川～毛呂 前面展望"), segment 2:13–3:08,
  CC BY 3.0, author Izumi5. Real front-cab video; 37 frames at 1.5 s, cropped to the
  cab window (`440:460:440:100`) to remove the train interior.
- COLMAP: 34 registered images, **993 points3D**, **4,460 observations**,
  median reprojection error **0.716 px**; all four gates passed.
- Package: `data/pointcloud/koma_bridge/`
  - `points.bin` 993 rows, 7 float32 values
  - `meta.json` site `koma_bridge`, `scale_status=relative`,
    `link_method=colmap_track`
  - `observations.npz` offsets/photo_idx/u/v/residual
  - `photos/` 34 source frames
  - `qa.json` all gates true
- UI verification: click at (735, 520) → panel shows 高麗川橋梁, scale relative,
  `colmap_track`, residual 0.28 px, V1/V2 source frames, marker on the track at the
  observed pixel. Source link and CC BY 3.0 attribution are shown.
- Honest limits: photogrammetric sparse cloud, relative scale, 2016 video, no GCP,
  no survey accuracy, no defect claims.

## 3. Mapillary adapter and trial

- API verified with the token from `.env` (values never printed or committed).
- Coverage query around Koma River Bridge: 74–87 perspective images in a 200 m bbox;
  images are real train-cab/rail views. Nebukawa 200 m bbox: 0 images. Tokyo bbox: 100+
  images. Coverage is location-dependent and not guaranteed.
- Adapter: `backend/app/modules/rail/mapillary.py`, CLI
  `acquire-mapillary`, same manifest contract. Token is read from
  `MAPILLARY_ACCESS_TOKEN` or `.env`; it is never logged.
- Trial work: `data/rail/koma_bridge_mapillary/` (87 images, 1600 px).
- COLMAP run: recorded separately when complete; use the same gates.

## 4. Reproducibility

Committed pipeline code at the exact remote commit is the source of truth. The video
adapter and Mapillary adapter normalize everything to:

```text
photos/*.jpg + manifest.json
  -> colmap.py (feature_extractor -> exhaustive_matcher -> mapper)
  -> points.bin + meta.json + observations.npz + photos/ + qa.json
```

The site-specific changes are only: site id/name, provider input, and optional crop.
The viewer/API stays unchanged except for observation-mode pick.

## 5. Fallbacks

If COLMAP produces a degenerate or empty model on another site:

1. try a same-sequence subset or a better crop;
2. try Mapillary if coverage exists;
3. only then evaluate a modern learned reconstruction (VGGT/Pi4/DUSt3R) and label the
   result `link_method=projected_unverified`; learned pointmaps do not provide observed
   track pixels, so their click-to-photo link needs a separate projection/visibility
   check.

## 6. Mapillary trial results

- API coverage around Koma River Bridge (200 m bbox): **87 perspective images**
  across 7 sequences, real train-cab/rail views. Nebukawa 200 m bbox: **0**; Tokyo:
  100+. Coverage is location-dependent.
- COLMAP on one 33-image sequence (`9yB9GtaVRQ6fQPNGBWmw9Q`): mapper failed to create
  a model (`colmap mapper` exit 1); matching finished but no usable initialization.
  This is recorded as a failed attempt, not a hidden result.
- VGGT fallback (16 evenly spaced frames from that sequence, 518 px, VGGT-1B,
  RTX 4060 Ti 16 GB):
  - device CUDA, dtype bfloat16; peak observed GPU ~15.3 GB;
  - 16 frames, **48,000 pointmap points**, each retaining its source pixel;
  - runtime ~128 s after model load;
  - package: `data/pointcloud/koma_vggt/`, `link_method=vggt_pointmap`,
    `scale_status=relative`, 16 frames;
  - limitation: the pointmap cloud collapses into a narrow corridor/line; it is a
    technical fallback for source-pixel linkage, not a replacement for the COLMAP
    package. No multi-view reprojection gate is claimed.
- Conclusion: Mapillary is a viable **discovery/coverage** provider where sequences exist,
  and a viable VGGT input; for this site, COLMAP on the continuous video is the better
  geometry package.

## 7. VGG-T³ latest-model trial

- Model: NVIDIA **VGG-T³** (`nvidia/vgg-ttt`), code `nv-dvl/vgg-ttt`, CVPR 2026.
- Input: 16 evenly spaced Koma frames (518 px, padded), memory-efficient inference.
- Runtime: model load + inference completed; **31,442 points**, 16 source frames,
  one source pixel per point; package `data/pointcloud/koma_vggt3/`,
  `link_method=vggt3_pointmap`, `scale_status=relative`.
- Result: technically runs on the 16 GB RTX 4060 Ti, but the pointmap collapses into a
  very compact blob; it is not a usable inspection surface and not promoted to primary.
- **Pi4 was not run yet.** The original VGGT-1B fallback was tested on Mapillary; VGG-T³
  is the latest tested model.
- Conclusion: newer feed-forward models alone do not fix the missing lateral viewpoints
  in this cab-view sequence. The next geometry step needs dense multi-view data or
  COLMAP dense/CUDA (the apt COLMAP is CPU-only and rejects dense stereo), not more
  points from the same thin baseline.

## 8. Multi-source + Mapillary SfM cluster (reusable path)

- `merge` CLI: one site can combine video frames, Mapillary, Commons, uploads; duplicates
  removed by sha256; each photo keeps provider/provenance. Koma merge
  (16 video + 16 Mapillary) = 32 photos; COLMAP mapper failed on this mixed set.
- Mapillary `sfm_cluster` (Graph API field) works:
  - example image `111709760985702` returned cluster `517747626077625`;
  - zlib payload: 1 camera, 46 shots, 7,322 points, reference LLA;
  - built `koma_sfm`: 6,041 points, 26 matched photos, 17,920 projected observations,
    project `mapillary_sfm_projected`, scale `relative`, no track residual gate;
  - **caveat**: the sampled cluster is street-level (the clicked point opens a road /
    houses photo), not a rail inspection surface. It is a working API/adapter result,
    not promoted to the rail demo.
- This proves the service works and is reusable; site/cluster selection needs a cluster
  whose shots actually observe the rail structure.

## 9. Dense Koma layer (COLMAP CUDA)

- Built COLMAP 3.11.1 with CUDA 12.1 and GCC 12 on the server.
- Dense pipeline on the 34 registered Koma frames:
  - `image_undistorter` (max 1000 px)
  - `patch_match_stereo` geometric, **4.2 min**
  - `stereo_fusion` → **43,750 fused points**
- Converted to `data/pointcloud/koma_bridge/dense.bin`; the viewer exposes
  **高密度 / Dense** as a separate layer.
- Sparse 993-point COLMAP tracks remain the **clickable** layer; dense is visual
  context only. Sparse coordinates and dense coordinates come from the same
  reconstruction.
- Result is visibly a rail corridor/bridge surface, but sparse and low-density
  (source frames are 440×460); relative scale, no GCP.

## 10. Pi4 trial

- Installed Pi4 (`yyfz/Pi4`) with Python 3.11, PyTorch 2.12.1 + CUDA 12.6.
- Input: 16 Koma frames, 512 px, geometry-only inference.
- Result: **27,437 points**, 16 source frames, one source pixel per point;
  `link_method=pi4_pointmap`, scale from Pi4 (`metric_scale≈2.8456`), labelled
  `relative`, no multi-view reprojection gate.
- Runtime ~89 s after model load; package `data/pointcloud/koma_pi4/`.
- Not promoted to the primary demo; the COLMAP sparse+dense Koma package remains primary.
