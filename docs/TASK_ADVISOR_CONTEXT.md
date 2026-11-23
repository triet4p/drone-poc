# Context for task-advisor — real image + real point cloud at a real site

Task ID: TASK-REAL-DATA-01
Date: 2026-11-23. This file is self-contained. It is NOT a request to implement; it is the
complete working context for a one-shot technical advice session.

## 1. User decision (latest, overrides earlier demo plan)

> "PHẢI LÀ ẢNH VÀ POINTCLOUD tại 1 địa điểm có thật. Có thể dựa vào merge 3d, pi4, osm,
> các map online. Chưa cần tính tên LICENSE, cái đó tính sẽ tìm giải pháp thay thế sau.
> Cho phép dùng cuda để test thử. với 1-2 cái. Trước đó, bạn có thể CUNG CẤP ĐỦ CÁC
> DOCUMENT, CONTEXT cho task-advisor subagent để nó suy nghĩ và đưa ra lời khuyên."

Interpretation:
- Must produce a demo where the **images are real photographs** and the **point cloud is
  real**, both from **one real, nameable location**.
- Click a point in the cloud → show the corresponding real photo (or a ranked set), not a
  rendered synthetic view.
- 1–2 test cases are enough.
- CUDA is allowed.
- License is explicitly deferred; do not spend the advice budget on license selection.
- Do NOT propose synthetic geometry + rendered views as the primary answer. It can only be
  a fallback with a visible label.

## 2. Existing application (what the new data must plug into)

Repo: `F:/DataImpact/drone-poc`; no git commits yet, all files untracked.

Stack:
- Backend: FastAPI + SQLite, Python 3.13 venv at `.venv`; serves React build.
- Frontend: React + Vite + MapLibre + Three.js; single page with tabs:
  飛行スケジュール / 撮影計画 / 点検確認 / 変位解析 / 保守優先度.
- 点検確認 has 3D / 点群 / 計測 / 写真 modes.
- AI: Grounding DINO tiny zero-shot, CPU, 6 reference images, 35 candidates currently.
- No real drone data yet. 6 reference photos are generic defect photos, not the point
  cloud source.

Current point-cloud contract (works end-to-end, but data is synthetic):
- `backend/app/pointcloud.py`
- Data directory `data/pointcloud/demo/`:
  - `points.bin`: float32, 7 floats/point: `x,y,z,r,g,b,member_idx`
  - `meta.json`: id, label, count, members, units, gauge_m, bounds, scale, views
  - `views.npz`: per-view depth buffer
  - `view_*.jpg`: 10 rendered views (1000×700), each with `eye`, `target`, `fov`
- API:
  - `GET /api/pointcloud/meta`
  - `GET /api/pointcloud/points.bin`
  - `GET /api/pointcloud/view/{id}`
  - `POST /api/pointcloud/pick` `{index, top_k}`
- Pick logic: project point into each view with look-at pinhole, test depth buffer,
  return `member`, `km`, local XYZ, `rail_offset_m`, `height_vs_rail_m`,
  `scale_status`, ranked views with pixel `u,v`.
- Frontend `frontend/src/components/PointCloudView.tsx`: Three.js Points, raycast,
  panel with metrics + view image + marker.
- Existing coordinate model: local metres, x along track from km 13150, z up, gauge
  1.067 m, rail top z=8.72. This is synthetic B-14.
- `docs/POINTCLOUD.md` documents the current synthetic approach.
- UI labels: 合成点群 / 相対形状 / 実測値ではない.

Important: the app already has the **interaction**, but its `views` are renders of the same
synthetic cloud. The new requirement is to replace this with a real site: real scan/cloud,
real photographs, real camera poses, and point→photo projection.

## 3. Research already done (do not redo from zero)

`docs/research/06a-pointcloud-sources.md`, `06b-multiview-dl.md` established:

- No open **rail corridor** point cloud exists for 根府川 / 小田原 with photos/poses.
  Kanagawa R1/R6 is airborne forest terrain, no underside/rail detail, no per-point photo.
  GSI point cloud is paid. xRoad MMS is DRM-locked. VIRTUAL SHIZUOKA is outside the area.
- ArchScanLib: 16 real UK railway masonry arch bridges, FARO scans, `.fls/.lsproj`,
  81.49 GB total, CC BY 4.0, **no photos, no camera poses**.
- OpenHeritage3D Alvord Lake Bridge: real concrete arch bridge, San Francisco, FARO
  terrestrial scan, **4.02 GB**, CC BY-NC-SA, **no original camera poses** (only a YouTube
  video).
- DL models: Pi4 (π⁴) gives pose + pointmap + track + mask, but requires CUDA, weights
  CC BY-NC 4.0; DUSt3R/MASt3R/VGGT/MapAnything are NC or partially NC; COLMAP+OpenMVS/ODM
  is the CPU fallback. License deferred by user.
- No public dataset combines a real bridge cloud with per-point photo IDs. Point-to-photo
  linkage must be reconstructed (COLMAP/Pi4) or built via proximity lookup.

## 4. Concrete candidate sites / data paths

### A. Alvord Lake Bridge, Golden Gate Park, San Francisco (real scan + real Commons photos)
- Point cloud: OpenHeritage3D project `n8mh-mm15`, DOI `10.26301/n8mh-mm15`,
  download via email link, 4.02 GB terrestrial FARO.
- Photos: Wikimedia Commons category `Alvord Lake Bridge` — 17 files, multiple angles,
  east/west, historic and 2020 images. Real photos of the exact structure.
- Plan: download scan; download Commons originals; infer camera poses with COLMAP or Pi4;
  align photo reconstruction to the metric FARO scan with control points / ICP / Umeyama;
  project scan points into photos with visibility test; serve real photo URLs.
- Strong points: guaranteed real geometry; no drone; no GCP; scan is metric; real photos.
- Weak points: not rail; 4 GB download; scan and photos may be decades apart (surface
  changes); only ~17 photos, overlap unknown; NC license; download requires request.
- Verdict hypothesis: lowest-risk path to satisfy the literal requirement, but weak
  storyline (not rail, not drone, not fresh).

### B. YouTube drone bridge inspection video + Pi4 (real video frames + reconstructed cloud)
- Candidate videos found:
  - `https://www.youtube.com/watch?v=lSuixx3fC84` "Lowlight Bridge Inspection with 4K Drone"
    (Skydio flies in/under/around bridges).
  - `https://www.youtube.com/watch?v=ZiEWlRegJ78` "How to conduct a Bridge Inspection with
    a Drone? DJI Matrice 30T" (may be edited/multi-cut).
- Plan: obtain a continuous 4K orbit/approach; extract 30–80 frames; run Pi4 on GPU; export
  pointmap/poses; keep original frames as source photos; project points into frames.
- Strong points: real images + real reconstruction; directly matches "drone × AI"; one
  pipeline for 1–2 cases; Pi4 gives pose+cloud.
- Weak points: video location/identity must be confirmed; YouTube download/license; cuts
  and motion blur destroy multiview; no GCP; scale is up-to-scale or predicted; 16 GB VRAM
  limits frame count; Pi4 install.
- Need an actual named bridge and continuous footage, not a highlight reel.

### C. Mapillary / KartaView sequence + OSM bridge
- Plan: choose a named OSM bridge with a dense street-level sequence; download geotagged
  images; run COLMAP/Pi4; use GPS as approximate georeference; OSM for structure identity.
- Strong: real photos, real GPS, real place, potentially many views.
- Weak: street-level coverage may only see one facade; bridge underside absent; API token;
  moving-car baseline/blur; no metric control; likely weak cloud.

### D. ArchScanLib real railway bridge + Commons/Geograph photos
- Plan: download one bridge subset from 81.49 GB; obtain real photos of that named bridge
  from Geograph/Wikimedia; infer photo poses; align to FARO scan; project.
- Strong: real rail bridge; metric FARO; commercial-friendly CC BY 4.0; best rail fidelity.
- Weak: download/subset extraction; photos may be few and non-overlapping; bridge names in
  dataset README must be mapped to photo coverage; no original poses.
- Verdict hypothesis: best "rail" answer if one bridge has enough photos; otherwise no
  clickable photo coverage.

### E. Merge 3D / fusion approaches
User mentions "merge 3d". Interpret as fusing sources:
1. Real scan (FARO) + real photo poses (COLMAP/Pi4) → best geometry + real appearance.
2. Drone photogrammetry + OSM footprint/alignment → georeference and context.
3. Two epochs / two clouds → change detection (future).
The advice should say which fusion is minimal for click-to-photo, and which is overkill.

### G. Landwasserviadukt, Switzerland (real rail viaduct + real 4K aerial video)
- Real named structure: Landwasser Viaduct, Rhaetian Railway, Graubünden, Switzerland.
- Wikimedia Commons: `File:Landwasserviadukt, aerial video.webm`, 310,529,873 bytes,
  3840×2160, 2016-08-25, CC BY-SA 4.0, author Capricorn4049. Continuous aerial video.
- Also `File:Wiesen Viaduct, aerial video.webm` (1920×1080, 574,910,631 bytes, CC BY-SA 4.0)
  and `File:Solis Viaduct, Schinschlucht and Solis dam, aerial video.webm` (4K, 343 MB).
- Plan: download 4K video; extract 30–60 sharp, overlapping frames; run Pi4; keep original
  frames as real source images; project points into frames. Named rail structure, no GCP;
  scale via known viaduct dimensions (e.g. Landwasser 65 m height / 136 m length / 6 arches)
  as a check, label relative unless verified.
- Strong: rail + drone + real site + real photos + no request/email; 310 MB; Commons
  attribution only; abundant still photos for cross-check.
- Weak: Pi4 install/reconstruction risk; video may contain cuts/gimbal motion; no GCP;
  large structure / texture-poor masonry; 16 GB VRAM limits frames; no real point cloud
  until reconstruction succeeds.
- Verdict hypothesis: best storyline and literal fit if Pi4 works; Alvord is lower-risk
  but not rail/drone.

### F. Rejected or low-value
- ArchScanLib cloud alone + rendered views: violates "real photos".
- OSM + satellite/aerial only: no multiview, no cloud.
- Kanagawa airborne + synthetic bridge: violates "real cloud at real site".
- Generic crack image datasets: no 3D, no site.
- ETH3D/Tanks and Temples: real images+poses+cloud, but not a bridge/site relevant to
  infrastructure; could be a technical fallback only.

## 5. Remote compute (verified 2026-11-23)

- SSH from Windows PowerShell 7: `ssh trietlm@192.168.99.214` (key auth works).
- Host `di-server`, Ubuntu 23.10, kernel 6.8, 12 vCPU, 62 GB RAM.
- GPU: NVIDIA RTX 4060 Ti, 16,380 MiB, driver 580.126.20.
- CUDA toolkit: `/usr/local/cuda-12.1`; `nvcc` exists there but not on PATH.
- Python 3.11.6; **torch is not installed** in system Python.
- Root filesystem `/dev/nvme0n1p2` 916 GB, 867 GB used, **2.4 GB free (100%)**.
- `/dev/shm` = 32 GB tmpfs (free). This is the only practical workspace for a multi-GB
  venv/model/download without freeing other users' data.
- Existing home contains many immutable `s18-*`/`s24-*` run directories and worktrees;
  treat as someone else's work; do not delete/reset.
- Local workstation: Windows, F: 167 GB with 17 GB free, C: 60 GB free; no CUDA; CPU
  torch 2.15; ffmpeg present; no yt-dlp, no COLMAP.

## 6. Constraints / unknowns

- Real place must be nameable; likely acceptable if not rail, but the demo is rail; state
  the tradeoff explicitly.
- Real photos must be at the same site; ideally the exact same structure, not "similar
  bridge".
- Click-to-photo needs camera intrinsics/extrinsics and occlusion handling. If only a few
  photos, a nearest-view/proximity lookup might be acceptable but must be labeled.
- No GCP/checkpoint; do not claim absolute survey accuracy. Pi4 may predict metric scale,
  but verify against a known dimension (gauge, span, barrier height) and label `relative`
  or `unverified`.
- 1–2 cases, timeboxed; prefer one strong case over two weak ones.
- Disk is the hard blocker on the remote host; `/dev/shm` is ephemeral and limited to
  32 GB. Advice must include a space plan.
- User wants advisor thinking first, not immediate implementation.

## 7. Decision the advisor must make

Answer these, in priority order:

1. **Pick the first case** (one, plus optional second) from A–D. Rank by:
   (a) literal compliance: real photos + real cloud at one real place;
   (b) click-to-photo feasibility;
   (c) time/space on 16 GB GPU and 2.4 GB disk;
   (d) demo credibility for a rail/structural engineering audience.
2. **Exact acquisition steps**: URLs/commands, expected sizes, what to download first,
   how to avoid 81 GB / 4 GB if possible; where to store (`/dev/shm` vs local F:).
3. **Reconstruction/linkage method**: Pi4 vs COLMAP vs manual control points; frame count;
   expected VRAM/time; how to align to an existing FARO scan; how to validate pose quality.
4. **Data contract**: how to map outputs into `points.bin + meta.json + views.npz`
   (or whether to switch to Potree/3D Tiles); what new fields are needed for real
   `photo_id`, `u,v`, `depth`, `visible`, `source_url`, `scale_status`.
5. **Minimal UI/API changes**; what can stay unchanged.
6. **Remote execution plan**: venv/model location, CUDA/PyTorch versions, install order,
   `/dev/shm` usage, cleanup, exact benchmark and acceptance checks.
7. **Verification protocol**: how to prove "this point → this real photo" is correct, with
   residuals/uncertainty; what to show on screen; what claims are forbidden.
8. **Kill criteria / fallback**: if Pi4 fails to install or reconstruction is garbage,
   what is the honest fallback? (Alvord scan+photos? one manual photo pair? stop and say
   data insufficient?)
9. **Risks**: licensing deferred, but note operational risks (YouTube ToS, Commons
   attribution, NC, download request delay, stale scan vs photos, non-rail typology).

## 8. Desired output from advisor

- A decision table for A–D with `real photo`, `real cloud`, `same site`, `rail`, `drone`,
  `click link`, `GPU`, `disk`, `time`, `risk`.
- One recommended path with a 1–2 day execution outline (not code).
- A short "do not do" list.
- The smallest acceptance test that proves the requirement.
- Open questions that genuinely need the user, only if unavoidable.
- Cite the concrete dataset/video URLs used.

Do not implement. Do not modify the repo. Read-only advice.
