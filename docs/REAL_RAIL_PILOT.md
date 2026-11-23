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
