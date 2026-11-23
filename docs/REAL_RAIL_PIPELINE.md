# Real rail point-cloud pipeline

Status: implementation started 2026-11-23. Task `TASK-REAL-DATA-02`.
Advisor: `RailJapanAdvisor`, consultation `C-20261123-02`.

## 1. Scope

Build a reusable pipeline for real photographs + a real point cloud at a real Japanese
rail site, with click-point → the actual source photograph and pixel that observed the
point. Drone is deferred. 1–2 pilot sites. License selection is deferred, but provenance
is recorded from the first fetch.

The promise is:

> Submit any Japanese rail site and get either a traceable package or a specific,
> recorded coverage/quality failure.

It is not a claim that public imagery can reconstruct every location.

## 2. Decision

- First pilot: **Yokokawa Station (横川駅), JR Shinetsu Line, Gunma**, Commons category
  `Category:Yokokawa Station` (53 files).
- Reuse test: **Nebukawa Station (根府川駅), JR Tokaido Line, Kanagawa**, category
  `Category:Nebukawa Station` (43 files) — same commands, different asset.
- Provider order: Commons category → Commons geosearch → optional Mapillary/KartaView →
  user upload. No token is required for the pilot.
- Reconstruction: COLMAP sparse (`feature_extractor` → `exhaustive_matcher` → `mapper`)
  on normalized stills; CPU baseline. Dense MVS/Pi4 later if needed.
- Linkage: only COLMAP track observations. No nearest-photo guess, no GPS-only link.
- Scale: `relative` by default; metric only with a documented site-specific reference.
- Viewer: keep Three.js picking; add observation-mode package.

## 3. CLI

The implementation lives under `backend/app/modules/rail/`:

```bash
python -m backend.app.modules.rail.cli acquire \
  --site-id yokokawa \
  --category "Category:Yokokawa Station" \
  --work data/rail/yokokawa \
  --width 1600

python -m backend.app.modules.rail.cli reconstruct \
  --site-id yokokawa \
  --work data/rail/yokokawa \
  --out data/pointcloud/yokokawa

python -m backend.app.modules.rail.cli inspect \
  --site-id yokokawa --work data/rail/yokokawa
```

For a coordinate query, `acquire --lat … --lon … --radius-m …` uses Commons geosearch.
OSM/Overpass resolution is best-effort; a timeout must be recorded, not silently treated
as “no coverage”.

## 4. Package contract

```text
data/pointcloud/<site_id>/
  points.bin          # float32, 7 per point: x,y,z,r,g,b,member_idx
  meta.json           # site, scale, provenance, photo table, views
  observations.npz    # offsets[n+1], photo_idx[], u[], v[], residual[]
  photos/             # exact normalized images served to the viewer
```

- `points.bin` row index is stable only within a package version.
- `photo_idx` indexes `meta.photos[]`; each photo has `photo_id`, `source_url`,
  `provider`, `provider_id`, `width`, `height`, `sha256`, `license`, `artist`.
- `u,v` are measured pixels in the exact served image, origin top-left.
- `residual` is the COLMAP track/point error available at export; do not present it as a
  calibrated measurement.
- `scale_status` is `relative` unless a site-specific metric anchor is documented.
- API `POST /api/pointcloud/pick` keeps `{index, top_k}` and returns observations sorted by
  residual. A future `site_id` parameter is reserved for multi-site serving.

## 5. Quality gates

Pilot is publishable only if:

- one connected model with ≥6 registered views;
- ≥200 retained static-structure points, each with ≥2 distinct image observations;
- median reprojection error ≤2 working-image pixels;
- for 10 spatially distributed points, 20/20 manual markers identify the same feature in
  two real photographs;
- the package rebuilds from the frozen manifest with unchanged point/photo associations.

If gates fail: record `insufficient_overlap` or `reconstruction_failed`, preserve the
manifest and rejected inputs, and stop. Do not lower the definition of a click or
substitute rendered views.

## 6. Remote execution

- Host `192.168.99.214`, user `trietlm`, PowerShell 7 OpenSSH.
- Ubuntu 23.10, 12 vCPU, 62 GB RAM, RTX 4060 Ti 16 GB, driver 580.126.20.
- 54 GB free on `/`; `/dev/shm` 32 GB; CUDA toolkit 12.1.
- COLMAP via apt `3.8-1build1`; CPU feature extraction/matching is the baseline.
- Pilot scratch cap 15 GB; keep ≥20 GB free. Do not touch other users' run directories.
- Sync exactly one pushed commit, run there, and copy back only manifests, package
  metadata, selected photos, logs and representative artifacts.

## 7. Inference

Grounding DINO tiny remains the inference stage. The reusable rule:

- run inference on registered, sufficiently detailed real photos;
- store detections against the exact `photo_id`;
- a detection box containing an observed pixel is a candidate association, not a
  confirmed 3D defect;
- engineer judgement stays append-only and separate from geometry.

Inference is not allowed to block publication of a valid photographic/geometry package.

## 8. Known limitations

- Commons photo coverage and overlap vary by site; categories include non-structure
  images (tickets, food, buses, signs).
- Mixed capture years can change the building; do not merge eras just to increase counts.
- No GCP: no survey-grade accuracy, no absolute height, no metre claims without a
  documented anchor.
- Sparse COLMAP may reconstruct only part of a large station.
- Mapillary token and Japan rail coverage remain unverified; KartaView samples returned
  zero images around Nebukawa/Tokyo.
